import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Hashable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from importlib import resources
from itertools import repeat
from pathlib import Path
from tempfile import TemporaryFile
from typing import BinaryIO, Never

from pydantic import ValidationError
from wireup import injectable

from ....extraction.extractors.models.duplicate_identity_error import DuplicateIdentityError
from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....extraction.extractors.models.extractor_error import ExtractorError
from ....extraction.extractors.models.extractor_failure_document import ExtractorFailureDocument
from ....extraction.extractors.models.extractor_runtime import ExtractorRuntime
from ....extraction.extractors.models.native_output_format import NativeOutputFormat
from ....extraction.extractors.models.source_parse_error import SourceParseError
from ....shared.code.contracts.identity_resolver import IdentityResolver
from ....shared.code.contracts.path_matcher import PathMatcher
from ....shared.code.models.failures.code_validation_error import CodeValidationError
from ....shared.code.models.immutable_code_record import ImmutableCodeRecord
from ....shared.code.models.immutable_code_value import ImmutableCodeValue
from ....shared.code.models.sources.identity import FileId, ImportIdentity
from ....shared.code.models.sources.identity_kind import IdentityKind
from ....shared.code.models.sources.scan_policy import ScanPolicy
from ....shared.code.models.sources.source_extraction import SourceExtraction
from ....shared.code.models.sources.source_file import SourceFile
from ....shared.values.models.value_reuse import ValueReuse
from ..batching.planner import SourceBatchPlanner
from ..domain import SourceReader
from ..models.extractor_contract_error import ExtractorContractError
from ..models.extractor_contract_violation import ExtractorContractViolation
from ..models.extractor_execution_error import ExtractorExecutionError
from ..models.extractor_resource_error import ExtractorResourceError
from ..models.extractor_unavailable_error import ExtractorUnavailableError
from ..models.invalid_source_root_error import InvalidSourceRootError
from ..models.source_access_error import SourceAccessError
from ..models.source_entry import SourceEntry
from ..models.source_observation import SourceObservation
from ..models.source_observation_invalidated_error import SourceObservationInvalidatedError
from ..transport.output_reader import ExtractorBatchOutputReader
from ..transport.source_file_factory import SourceFileFactory
from .source_manifest_builder import SourceManifestBuilder


@injectable(as_type=SourceReader)
@dataclass(frozen=True)
class BatchSourceReader(SourceReader):
    identities: IdentityResolver
    files: SourceFileFactory
    paths: PathMatcher
    manifests: SourceManifestBuilder
    output: ExtractorBatchOutputReader
    planners: Mapping[Hashable, SourceBatchPlanner]

    def ensure_available(self, runtime: ExtractorRuntime) -> None:
        executable = runtime.command[0]
        if shutil.which(executable) is None:
            raise ExtractorUnavailableError(runtime.descriptor.language, executable)

    def has_source_files(self, request: ExtractionRequest, policy: ScanPolicy) -> bool:
        root = Path(request.root)
        try:
            resolved_root = root.resolve()
            if not resolved_root.is_dir():
                raise InvalidSourceRootError(str(root))
            source_paths, _, _ = self._discover_source_files(request, resolved_root, policy, limit=1)
        except OSError as error:
            raise SourceAccessError(str(root), "inspect") from error
        return bool(source_paths)

    def extract_source(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceExtraction:
        observation = self.observe(request, policy)
        files = self.extract_observed_entries(observation, tuple(entry.source_id for entry in observation.entries))
        import_identities: dict[ImportIdentity, FileId] = {}
        for file_id, source_file in files.items():
            existing = import_identities.get(source_file.import_identity)
            if existing is not None:
                raise DuplicateIdentityError(IdentityKind.IMPORT, source_file.import_identity, existing, file_id)
            import_identities[source_file.import_identity] = file_id
        return SourceExtraction.model_construct(
            files=files,
            import_identities=import_identities,
            manifest=observation.manifest,
            files_found=observation.files_found,
            files_excluded=observation.files_excluded,
            directories_pruned=observation.directories_pruned,
        ).validate_manifest_sources()

    def observe(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceObservation:
        root = Path(request.root)
        try:
            resolved_root = root.resolve()
            if not resolved_root.is_dir():
                raise InvalidSourceRootError(str(root))
            request = request.model_copy(update={"root": str(resolved_root)})
            source_paths, files_excluded, directories_pruned = self._discover_source_files(
                request, resolved_root, policy, limit=None
            )
            with ThreadPoolExecutor(max_workers=request.batch_config.max_workers) as executor:
                entries = tuple(executor.map(self.observe_entry, repeat(resolved_root), source_paths))
        except OSError as error:
            raise SourceAccessError(str(root), "observe") from error
        runtime = self.manifests.observe(request)
        return SourceObservation.model_construct(
            request=request,
            entries=entries,
            files_found=len(source_paths),
            files_excluded=files_excluded,
            directories_pruned=directories_pruned,
            manifest=self.manifests.build(policy, runtime, entries),
        )

    def extract_entries(
        self, observation: SourceObservation, source_ids: tuple[FileId, ...]
    ) -> dict[FileId, SourceFile]:
        self.validate_observation(observation)
        return self.extract_observed_entries(observation, source_ids)

    def extract_observed_entries(
        self, observation: SourceObservation, source_ids: tuple[FileId, ...]
    ) -> dict[FileId, SourceFile]:
        request = observation.request
        requested = set(source_ids)
        entries = tuple(entry for entry in observation.entries if entry.source_id in requested)
        if len(entries) != len(requested):
            missing = tuple(sorted(requested - {entry.source_id for entry in entries}, key=str))
            raise ExtractorContractError(
                request.runtime.descriptor.language,
                ExtractorContractViolation.SOURCE_SET_MISMATCH,
                missing,
                (),
                (),
                "source observation does not contain requested identities",
            )
        root = Path(request.root)
        files: dict[FileId, SourceFile] = {}
        plan = self.planners[request.batch_config.planner].plan(entries, request.batch_config)
        try:
            if plan.parallel:
                with ThreadPoolExecutor(max_workers=request.batch_config.max_workers) as executor:
                    for extracted in executor.map(self._extract_batch, repeat(request), repeat(root), plan.batches):
                        self._merge_files(files, extracted)
            else:
                for batch_entries in plan.batches:
                    self._merge_files(files, self._extract_batch(request, root, batch_entries))
        except (ExtractorError, SourceAccessError):
            self.validate_observation(observation)
            raise
        self.validate_observation(observation)
        return {entry.source_id: files[entry.source_id] for entry in entries}

    def validate_observation(self, observation: SourceObservation) -> None:
        root = Path(observation.request.root)
        try:
            current_paths, _, _ = self._discover_source_files(
                observation.request,
                root,
                observation.manifest.policy,
                limit=None,
            )
            with ThreadPoolExecutor(max_workers=observation.request.batch_config.max_workers) as executor:
                current = {
                    path.relative_to(root).as_posix(): content_digest
                    for path, content_digest in zip(
                        current_paths, executor.map(self.read_digest, current_paths), strict=True
                    )
                }
        except OSError as error:
            raise SourceAccessError(str(root), "validate observation for") from error
        observed = {entry.relative_path: (entry.source_id, entry.content_digest) for entry in observation.entries}
        added = tuple(
            sorted(
                (self.identities.file_id(str(root), str(root / path)) for path in current.keys() - observed.keys()),
                key=str,
            )
        )
        removed = tuple(sorted((observed[path][0] for path in observed.keys() - current.keys()), key=str))
        changed = tuple(
            sorted(
                (observed[path][0] for path in current.keys() & observed.keys() if current[path] != observed[path][1]),
                key=str,
            )
        )
        if added or removed or changed:
            raise SourceObservationInvalidatedError(added, removed, changed)

    def _discover_source_files(
        self, request: ExtractionRequest, root: Path, policy: ScanPolicy, limit: int | None
    ) -> tuple[list[Path], int, int]:
        source_paths: list[Path] = []
        files_excluded = 0
        directories_pruned = 0
        extensions = request.runtime.file_extensions
        visited_directories: set[tuple[int, int]] = set()
        for current_root, dir_names, file_names in os.walk(
            root,
            followlinks=policy.follow_symlinks,
            onerror=self.raise_source_access_error,
        ):
            current_path = Path(current_root)
            if policy.follow_symlinks:
                status = current_path.stat()
                identity = (status.st_dev, status.st_ino)
                if identity in visited_directories:
                    directories_pruned += 1
                    dir_names.clear()
                    continue
                visited_directories.add(identity)
            included_directories: list[str] = []
            for dir_name in dir_names:
                directory = current_path / dir_name
                if self._is_excluded_path(policy, root, directory):
                    directories_pruned += 1
                else:
                    included_directories.append(dir_name)
            dir_names[:] = included_directories
            for file_name in file_names:
                file_path = current_path / file_name
                if file_path.suffix.lower() in extensions:
                    if self._is_excluded_path(policy, root, file_path):
                        files_excluded += 1
                    else:
                        source_paths.append(file_path.absolute())
                        if limit is not None and len(source_paths) >= limit:
                            return (sorted(source_paths), files_excluded, directories_pruned)
        return (sorted(source_paths), files_excluded, directories_pruned)

    def raise_source_access_error(self, error: OSError) -> None:
        path = error.filename or "unknown"
        raise SourceAccessError(path, "walk") from error

    def _is_excluded_path(self, policy: ScanPolicy, root: Path, path: Path) -> bool:
        if not policy.excluded_patterns:
            return False
        relative_path = path.relative_to(root).as_posix()
        return any(
            self.paths.match(relative_path, pattern, scope=True) is not None for pattern in policy.excluded_patterns
        )

    def _extract_batch(
        self,
        request: ExtractionRequest,
        root: Path,
        entries: tuple[SourceEntry, ...],
    ) -> dict[FileId, SourceFile]:
        if not entries:
            return {}
        runtime = request.runtime
        entrypoint = runtime.entrypoint
        try:
            script_path = Path(str(resources.files(entrypoint.package).joinpath(entrypoint.path)))
        except (ImportError, OSError) as error:
            raise ExtractorResourceError(runtime.descriptor.language, entrypoint.path) from error
        if not script_path.is_file():
            raise ExtractorResourceError(runtime.descriptor.language, str(script_path))
        paths_by_source_id = {entry.source_id: entry.path for entry in entries}
        command = [*runtime.command, *entrypoint.command_arguments(script_path), "--batch", str(root)]
        return self.run_batch(runtime, command, paths_by_source_id, str(root))

    def run_batch(
        self, runtime: ExtractorRuntime, command: list[str], sources: Mapping[FileId, str], root: str
    ) -> dict[FileId, SourceFile]:
        language = runtime.descriptor.language
        try:
            with TemporaryFile() as diagnostics:
                with subprocess.Popen(
                    command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=diagnostics
                ) as process:
                    reuse = ValueReuse[ImmutableCodeValue | ImmutableCodeRecord](
                        indexed=runtime.output_format is NativeOutputFormat.INDEXED_JSONL
                    )
                    extracted: dict[FileId, SourceFile] = {}
                    seen_source_ids: set[FileId] = set()
                    duplicate_source_ids: set[FileId] = set()
                    try:
                        if process.stdin is None or process.stdout is None:
                            raise ExtractorExecutionError(language, -1, "extractor process pipes are unavailable")
                        try:
                            process.stdin.write(json.dumps(sources).encode("utf-8"))
                            process.stdin.close()
                            for line in process.stdout:
                                source_id, parsed = self.output.read(line, reuse)
                                if source_id in seen_source_ids:
                                    duplicate_source_ids.add(source_id)
                                else:
                                    seen_source_ids.add(source_id)
                                    if source_id in sources:
                                        extracted[source_id] = self.files.create(
                                            source_id,
                                            self.identities.import_identity(root, sources[source_id]),
                                            parsed,
                                        )
                                del parsed
                        except (ValidationError, CodeValidationError, BrokenPipeError):
                            for _ in process.stdout:
                                pass
                            self.validate_process(language, process, diagnostics)
                            raise
                        self.validate_process(language, process, diagnostics)
                        if duplicate_source_ids:
                            raise ExtractorContractError(
                                language,
                                ExtractorContractViolation.DUPLICATE_SOURCE_IDENTITY,
                                (),
                                (),
                                tuple(sorted(duplicate_source_ids, key=str)),
                                "extractor output contains duplicate source identities",
                            )
                        expected = set(sources)
                        if seen_source_ids != expected:
                            raise ExtractorContractError(
                                language,
                                ExtractorContractViolation.SOURCE_SET_MISMATCH,
                                tuple(sorted(expected - seen_source_ids, key=str)),
                                tuple(sorted(seen_source_ids - expected, key=str)),
                                (),
                                "extractor output identities do not match the requested batch",
                            )
                        return extracted
                    finally:
                        reuse.clear()
                        if process.poll() is None:
                            process.kill()
                        process.wait()
        except OSError as error:
            raise ExtractorExecutionError(language, -1, str(error)) from error
        except ValidationError as error:
            raise ExtractorContractError(
                language,
                ExtractorContractViolation.INVALID_OUTPUT,
                (),
                (),
                (),
                str(error),
            ) from error

    def validate_process(self, language: str, process: subprocess.Popen[bytes], diagnostics: BinaryIO) -> None:
        exit_code = process.wait()
        if exit_code == 0:
            return
        diagnostics.seek(0)
        try:
            message = diagnostics.read().decode("utf-8").strip()
        except UnicodeDecodeError as error:
            raise ExtractorExecutionError(language, exit_code, f"invalid UTF-8 stderr: {error}") from error
        execution_error = ExtractorExecutionError(language, exit_code, message)
        marker = "modwire-error:"
        failure_documents = tuple(line.removeprefix(marker) for line in message.splitlines() if line.startswith(marker))
        if failure_documents:
            if len(failure_documents) != 1:
                raise ExtractorContractError(
                    language,
                    ExtractorContractViolation.INVALID_OUTPUT,
                    (),
                    (),
                    (),
                    "extractor emitted multiple failure documents",
                ) from execution_error
            self.raise_extractor_failure(failure_documents[0], execution_error)
        raise execution_error

    def raise_extractor_failure(self, document: str, execution_error: ExtractorExecutionError) -> Never:
        try:
            failure = ExtractorFailureDocument.model_validate_json(document)
        except ValidationError as error:
            raise ExtractorContractError(
                execution_error.language,
                ExtractorContractViolation.INVALID_OUTPUT,
                (),
                (),
                (),
                str(error),
            ) from error
        if failure.language != execution_error.language:
            raise ExtractorContractError(
                execution_error.language,
                ExtractorContractViolation.INVALID_OUTPUT,
                (),
                (),
                (),
                "extractor failure document language does not match its runtime",
            ) from execution_error
        raise SourceParseError(
            failure.language,
            failure.path,
            failure.line,
            failure.column,
            failure.diagnostic,
        ) from execution_error

    def _merge_files(self, files: dict[FileId, SourceFile], extracted: dict[FileId, SourceFile]) -> None:
        for file_id, source_file in extracted.items():
            if file_id in files:
                raise DuplicateIdentityError(IdentityKind.FILE, file_id, file_id, file_id)
            files[file_id] = source_file

    def observe_entry(self, root: Path, path: Path) -> SourceEntry:
        content = path.read_bytes()
        line_count = content.count(b"\n") + content.count(b"\r") - content.count(b"\r\n")
        if content and not content.endswith((b"\n", b"\r")):
            line_count += 1
        return SourceEntry(
            source_id=self.identities.file_id(str(root), str(path)),
            relative_path=path.relative_to(root).as_posix(),
            content_digest=self.digest(content),
            path=str(path),
            line_count=line_count,
        )

    def read_digest(self, path: Path) -> str:
        return self.digest(path.read_bytes())

    def digest(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
