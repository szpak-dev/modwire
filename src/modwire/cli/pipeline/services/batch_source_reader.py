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

from wireup import injectable

from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....extraction.extractors.models.extractor_runtime import ExtractorRuntime
from ....shared.code.application import CodeApplication
from ....shared.code.domain import PathMatcher
from ....shared.code.models.duplicate_identity_error import DuplicateIdentityError
from ....shared.code.models.identity import FileId, ModuleId
from ....shared.code.models.scan_policy import ScanPolicy
from ....shared.code.models.source_extraction import SourceExtraction
from ....shared.code.models.source_file import SourceFile
from ..batching.planner import SourceBatchPlanner
from ..domain import SourceReader
from ..models.source_entry import SourceEntry
from ..models.source_inventory import SourceInventory
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
            raise RuntimeError(
                f"{runtime.descriptor.language} extractor runtime is not available on PATH: {executable}"
            )

    def has_source_files(self, request: ExtractionRequest, policy: ScanPolicy) -> bool:
        root = Path(request.root)
        resolved_root = root.resolve()
        if not resolved_root.is_dir():
            raise ValueError(f"Source root is not a directory: {root}")
        source_paths, _, _ = self._discover_source_files(request, resolved_root, policy, limit=1)
        return bool(source_paths)

    def extract_source(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceExtraction:
        inventory = self.inventory(request, policy)
        files = self.extract_entries(request, inventory, tuple(entry.source_id for entry in inventory.entries))
        modules: dict[ModuleId, FileId] = {}
        for file_id, source_file in files.items():
            existing = modules.get(source_file.module_id)
            if existing is not None:
                raise DuplicateIdentityError("module", source_file.module_id, existing, file_id)
            modules[source_file.module_id] = file_id
        return SourceExtraction(
            files=files,
            modules=modules,
            manifest=inventory.manifest,
            files_found=inventory.files_found,
            files_excluded=inventory.files_excluded,
            directories_pruned=inventory.directories_pruned,
        )

    def inventory(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceInventory:
        root = Path(request.root)
        resolved_root = root.resolve()
        if not resolved_root.is_dir():
            raise ValueError(f"Source root is not a directory: {root}")
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
        runtime = self.manifests.observe(request)
        return SourceInventory(
            entries=entries,
            files_found=len(source_paths),
            files_excluded=files_excluded,
            directories_pruned=directories_pruned,
            manifest=self.manifests.build(policy, runtime, entries),
        )

    def extract_entries(
        self, request: ExtractionRequest, inventory: SourceInventory, source_ids: tuple[FileId, ...]
    ) -> dict[FileId, SourceFile]:
        requested = set(source_ids)
        entries = tuple(entry for entry in inventory.entries if entry.source_id in requested)
        if len(entries) != len(requested):
            missing = sorted(str(source_id) for source_id in requested - {entry.source_id for entry in entries})
            raise ValueError(f"Source inventory does not contain requested identities: {missing}")
        root = Path(request.root).resolve()
        source_paths = tuple(Path(entry.path) for entry in entries)
        files: dict[FileId, SourceFile] = {}
        plan = self.planners[request.batch_config.planner].plan(source_paths, request.batch_config)
        if plan.parallel:
            with ThreadPoolExecutor(max_workers=request.batch_config.max_workers) as executor:
                for extracted in executor.map(self._extract_batch, repeat(request), repeat(root), plan.batches):
                    self._merge_files(files, extracted)
        else:
            for batch_paths in plan.batches:
                self._merge_files(files, self._extract_batch(request, root, batch_paths))
        expected_digests = {entry.source_id: entry.content_digest for entry in entries}
        for source_path in source_paths:
            source_id = self._source_id_for_path(request, root, source_path)
            if self._content_digest(source_path) != expected_digests[source_id]:
                raise RuntimeError(f"Source file changed during extraction: {source_id}")
        return {entry.source_id: files[entry.source_id] for entry in entries}

    def _discover_source_files(
        self, request: ExtractionRequest, root: Path, policy: ScanPolicy, limit: int | None
    ) -> tuple[list[Path], int, int]:
        source_paths: list[Path] = []
        files_excluded = 0
        directories_pruned = 0
        extensions = request.runtime.file_extensions
        visited_directories: set[tuple[int, int]] = set()
        for current_root, dir_names, file_names in os.walk(root, followlinks=policy.follow_symlinks):
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
        entrypoint = runtime.resources.entrypoint
        script_path = Path(str(resources.files(entrypoint.package).joinpath(entrypoint.path)))
        if not script_path.is_file():
            raise RuntimeError(f"{runtime.descriptor.language} extractor script is missing: {script_path}")
        paths_by_source_id = {
            self.code.file_id(str(root), str(source_path)): str(source_path) for source_path in source_paths
        }
        command = [*runtime.command, str(script_path), "--batch", str(root)]
        if request.batch_config.output_format == "jsonl":
            command.append("--jsonl")
        completed = subprocess.run(
            command, input=json.dumps(paths_by_source_id), text=True, capture_output=True, check=False
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(
                f"{runtime.descriptor.language} extractor failed with exit code {completed.returncode}: {message}"
            )
        extracted = self.outputs[request.batch_config.output_format].read(completed.stdout)
        source_paths_by_id = {
            self.code.file_id(str(root), str(source_path)): source_path for source_path in source_paths
        }
        extracted_files: dict[FileId, SourceFile] = {}
        for file_id, parsed_source_file in extracted.items():
            source_path = source_paths_by_id[file_id]
            extracted_files[file_id] = self.files.create(
                file_id,
                self.code.module_id(str(root), str(source_path)),
                parsed_source_file,
            )
        return extracted_files

    def _merge_files(self, files: dict[FileId, SourceFile], extracted: dict[FileId, SourceFile]) -> None:
        for file_id, source_file in extracted.items():
            if file_id in files:
                raise DuplicateIdentityError("file", file_id, file_id, file_id)
            files[file_id] = source_file

    def _source_id_for_path(self, request: ExtractionRequest, root: Path, path: Path) -> FileId:
        return self.code.file_id(str(root), str(path))

    def _content_digest(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
