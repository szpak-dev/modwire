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

from pydantic import ValidationError
from wireup import injectable

from ....extraction.extractors.models.batch_output_format import BatchOutputFormat
from ....extraction.extractors.models.duplicate_identity_error import DuplicateIdentityError
from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....extraction.extractors.models.extractor_error import ExtractorError
from ....extraction.extractors.models.extractor_runtime import ExtractorRuntime
from ....shared.code.application import CodeApplication
from ....shared.code.domain import PathMatcher
from ....shared.code.models.identity import FileId, ImportIdentity
from ....shared.code.models.identity_kind import IdentityKind
from ....shared.code.models.scan_policy import ScanPolicy
from ....shared.code.models.source_extraction import SourceExtraction
from ....shared.code.models.source_file import SourceFile
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
    code: CodeApplication
    files: SourceFileFactory
    paths: PathMatcher
    manifests: SourceManifestBuilder
    outputs: Mapping[Hashable, ExtractorBatchOutputReader]
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
        files = self.extract_entries(observation, tuple(entry.source_id for entry in observation.entries))
        import_identities: dict[ImportIdentity, FileId] = {}
        for file_id, source_file in files.items():
            existing = import_identities.get(source_file.import_identity)
            if existing is not None:
                raise DuplicateIdentityError(IdentityKind.IMPORT, source_file.import_identity, existing, file_id)
            import_identities[source_file.import_identity] = file_id
        return SourceExtraction(
            files=files,
            import_identities=import_identities,
            manifest=observation.manifest,
            files_found=observation.files_found,
            files_excluded=observation.files_excluded,
            directories_pruned=observation.directories_pruned,
        )

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
            entries = tuple(
                SourceEntry(
                    source_id=self._source_id_for_path(request, resolved_root, source_path),
                    relative_path=source_path.relative_to(resolved_root).as_posix(),
                    content_digest=self._content_digest(source_path),
                    path=str(source_path),
                )
                for source_path in source_paths
            )
        except OSError as error:
            raise SourceAccessError(str(root), "observe") from error
        runtime = self.manifests.observe(request)
        return SourceObservation(
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
        try:
            root = Path(request.root).resolve()
        except OSError as error:
            raise SourceAccessError(request.root, "resolve") from error
        source_paths = tuple(Path(entry.path) for entry in entries)
        files: dict[FileId, SourceFile] = {}
        plan = self.planners[request.batch_config.planner].plan(source_paths, request.batch_config)
        self.validate_observation(observation)
        try:
            if plan.parallel:
                with ThreadPoolExecutor(max_workers=request.batch_config.max_workers) as executor:
                    for extracted in executor.map(self._extract_batch, repeat(request), repeat(root), plan.batches):
                        self._merge_files(files, extracted)
            else:
                for batch_paths in plan.batches:
                    self._merge_files(files, self._extract_batch(request, root, batch_paths))
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
            current = {
                path.relative_to(root).as_posix(): (
                    self._source_id_for_path(observation.request, root, path),
                    self._content_digest(path),
                )
                for path in current_paths
            }
        except OSError as error:
            raise SourceAccessError(str(root), "validate observation for") from error
        observed = {entry.relative_path: (entry.source_id, entry.content_digest) for entry in observation.entries}
        added = tuple(sorted((current[path][0] for path in current.keys() - observed.keys()), key=str))
        removed = tuple(sorted((observed[path][0] for path in observed.keys() - current.keys()), key=str))
        changed = tuple(
            sorted(
                (
                    observed[path][0]
                    for path in current.keys() & observed.keys()
                    if current[path][1] != observed[path][1]
                ),
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
        relative_path = path.relative_to(root).as_posix()
        return any(
            self.paths.match(relative_path, pattern, scope=True) is not None for pattern in policy.excluded_patterns
        )

    def _extract_batch(
        self, request: ExtractionRequest, root: Path, source_paths: tuple[Path, ...]
    ) -> dict[FileId, SourceFile]:
        if not source_paths:
            return {}
        runtime = request.runtime
        entrypoint = runtime.entrypoint
        try:
            script_path = Path(str(resources.files(entrypoint.package).joinpath(entrypoint.path)))
        except (ImportError, OSError) as error:
            raise ExtractorResourceError(runtime.descriptor.language, entrypoint.path) from error
        if not script_path.is_file():
            raise ExtractorResourceError(runtime.descriptor.language, str(script_path))
        paths_by_source_id = {
            self.code.file_id(str(root), str(source_path)): str(source_path) for source_path in source_paths
        }
        command = [*runtime.command, str(script_path), "--batch", str(root)]
        if request.batch_config.output_format is BatchOutputFormat.JSON_LINES:
            command.append("--jsonl")
        try:
            completed = subprocess.run(
                command, input=json.dumps(paths_by_source_id), text=True, capture_output=True, check=False
            )
        except OSError as error:
            raise ExtractorExecutionError(runtime.descriptor.language, -1, str(error)) from error
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise ExtractorExecutionError(runtime.descriptor.language, completed.returncode, message)
        try:
            extracted = self.outputs[request.batch_config.output_format].read(completed.stdout)
        except ValidationError as error:
            raise ExtractorContractError(
                runtime.descriptor.language,
                ExtractorContractViolation.INVALID_OUTPUT,
                (),
                (),
                (),
                str(error),
            ) from error
        source_ids = tuple(source_id for source_id, _ in extracted)
        seen_source_ids: set[FileId] = set()
        duplicate_source_ids: set[FileId] = set()
        for source_id in source_ids:
            if source_id in seen_source_ids:
                duplicate_source_ids.add(source_id)
            else:
                seen_source_ids.add(source_id)
        if duplicate_source_ids:
            raise ExtractorContractError(
                runtime.descriptor.language,
                ExtractorContractViolation.DUPLICATE_SOURCE_IDENTITY,
                (),
                (),
                tuple(sorted(duplicate_source_ids, key=str)),
                "extractor output contains duplicate source identities",
            )
        extracted_by_source_id = dict(extracted)
        source_paths_by_id = {
            self.code.file_id(str(root), str(source_path)): source_path for source_path in source_paths
        }
        expected = set(source_paths_by_id)
        actual = set(extracted_by_source_id)
        if actual != expected:
            raise ExtractorContractError(
                runtime.descriptor.language,
                ExtractorContractViolation.SOURCE_SET_MISMATCH,
                tuple(sorted(expected - actual, key=str)),
                tuple(sorted(actual - expected, key=str)),
                (),
                "extractor output identities do not match the requested batch",
            )
        extracted_files: dict[FileId, SourceFile] = {}
        try:
            for file_id, parsed_source_file in extracted_by_source_id.items():
                source_path = source_paths_by_id[file_id]
                extracted_files[file_id] = self.files.create(
                    file_id,
                    self.code.import_identity(str(root), str(source_path)),
                    parsed_source_file,
                )
        except ValidationError as error:
            raise ExtractorContractError(
                runtime.descriptor.language,
                ExtractorContractViolation.INVALID_OUTPUT,
                (),
                (),
                (),
                str(error),
            ) from error
        return extracted_files

    def _merge_files(self, files: dict[FileId, SourceFile], extracted: dict[FileId, SourceFile]) -> None:
        for file_id, source_file in extracted.items():
            if file_id in files:
                raise DuplicateIdentityError(IdentityKind.FILE, file_id, file_id, file_id)
            files[file_id] = source_file

    def _source_id_for_path(self, request: ExtractionRequest, root: Path, path: Path) -> FileId:
        return self.code.file_id(str(root), str(path))

    def _content_digest(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
