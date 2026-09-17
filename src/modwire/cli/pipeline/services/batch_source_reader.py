import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from importlib import resources
from itertools import repeat
from pathlib import Path
from typing import Any, cast

from wireup import injectable

from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....extraction.extractors.models.extractor_runtime import ExtractorRuntime
from ....shared.code.application import CodeApplication
from ....shared.code.domain import PathMatcher
from ....shared.code.models.duplicate_identity_error import DuplicateIdentityError
from ....shared.code.models.identity import FileId, ModuleId
from ....shared.code.models.source_extraction import SourceExtraction
from ....shared.code.models.source_file import SourceFile
from ..domain import SourceReader


@injectable(as_type=SourceReader)
@dataclass(frozen=True)
class BatchSourceReader(SourceReader):
    code: CodeApplication
    paths: PathMatcher
    excluded_dir_names = frozenset(
        {
            ".git",
            ".hg",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".svn",
            ".venv",
            "__pycache__",
            "build",
            "coverage",
            "dist",
            "ignored",
            "node_modules",
            "vendor",
        }
    )

    def ensure_available(self, runtime: ExtractorRuntime) -> None:
        executable = runtime.command[0]
        if shutil.which(executable) is None:
            raise RuntimeError(f"{runtime.language} extractor runtime is not available on PATH: {executable}")

    def has_source_files(self, request: ExtractionRequest) -> bool:
        root = Path(request.root)
        resolved_root = root.resolve()
        if not resolved_root.is_dir():
            raise ValueError(f"Source root is not a directory: {root}")
        source_paths, _ = self._discover_source_files(request, resolved_root)
        return bool(source_paths)

    def extract_source(self, request: ExtractionRequest) -> SourceExtraction:
        root = Path(request.root)
        resolved_root = root.resolve()
        if not resolved_root.is_dir():
            raise ValueError(f"Source root is not a directory: {root}")
        source_paths, files_excluded = self._discover_source_files(request, resolved_root)
        files: dict[FileId, SourceFile] = {}
        batches = self._source_batches(request, source_paths)
        if self._uses_parallel_batches(request, len(source_paths)):
            max_workers = max(1, request.batch_config.max_workers)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for extracted in executor.map(self._extract_batch, repeat(request), repeat(resolved_root), batches):
                    self._merge_files(files, extracted)
        else:
            for batch_paths in batches:
                self._merge_files(files, self._extract_batch(request, resolved_root, batch_paths))
        modules: dict[ModuleId, FileId] = {}
        for file_id, source_file in files.items():
            existing = modules.get(source_file.module_id)
            if existing is not None:
                raise DuplicateIdentityError("module", source_file.module_id, existing, file_id)
            modules[source_file.module_id] = file_id
        return SourceExtraction(
            files=files, modules=modules, files_found=len(source_paths), files_excluded=files_excluded
        )

    def _source_batches(self, request: ExtractionRequest, source_paths: list[Path]) -> list[list[Path]]:
        batch_size = self._batch_size(request, len(source_paths))
        return [source_paths[start : start + batch_size] for start in range(0, len(source_paths), batch_size)]

    def _batch_size(self, request: ExtractionRequest, source_count: int) -> int:
        if self._uses_parallel_batches(request, source_count) and request.batch_config.parallel_size:
            return max(1, request.batch_config.parallel_size)
        return max(1, request.batch_config.size)

    def _uses_parallel_batches(self, request: ExtractionRequest, source_count: int) -> bool:
        return (
            request.batch_config.parallel_threshold > 0
            and source_count >= request.batch_config.parallel_threshold
            and (request.batch_config.max_workers > 1)
        )

    def _discover_source_files(self, request: ExtractionRequest, root: Path) -> tuple[list[Path], int]:
        source_paths: list[Path] = []
        files_excluded = 0
        extensions = request.runtime.file_extensions
        for current_root, dir_names, file_names in os.walk(root):
            current_path = Path(current_root)
            excluded_dirs = [
                dir_name
                for dir_name in dir_names
                if self._is_excluded_dir(request, dir_name)
                or self._is_excluded_path(request, root, current_path / dir_name)
            ]
            files_excluded += sum(
                self._count_source_files(request, current_path / dir_name) for dir_name in excluded_dirs
            )
            dir_names[:] = [dir_name for dir_name in dir_names if dir_name not in excluded_dirs]
            for file_name in file_names:
                file_path = current_path / file_name
                if file_path.suffix.lower() in extensions:
                    if self._is_excluded_path(request, root, file_path):
                        files_excluded += 1
                    else:
                        source_paths.append(file_path.resolve())
        return (sorted(source_paths), files_excluded)

    def _count_source_files(self, request: ExtractionRequest, root: Path) -> int:
        count = 0
        extensions = request.runtime.file_extensions
        for current_root, dir_names, file_names in os.walk(root):
            dir_names[:] = [dir_name for dir_name in dir_names if not self._is_excluded_dir(request, dir_name)]
            count += sum(1 for file_name in file_names if (Path(current_root) / file_name).suffix.lower() in extensions)
        return count

    def _is_excluded_dir(self, request: ExtractionRequest, name: str) -> bool:
        return name in self.excluded_dir_names or name.startswith(".")

    def _is_excluded_path(self, request: ExtractionRequest, root: Path, path: Path) -> bool:
        relative_path = path.relative_to(root).as_posix()
        return any(
            self.paths.match(relative_path, pattern, scope=True) is not None for pattern in request.excluded_patterns
        )

    def _extract_batch(
        self, request: ExtractionRequest, root: Path, source_paths: list[Path]
    ) -> dict[FileId, SourceFile]:
        if not source_paths:
            return {}
        runtime = request.runtime
        script_path = Path(str(resources.files("modwire.cli.resources").joinpath("extractors", runtime.resource)))
        if not script_path.is_file():
            raise RuntimeError(f"{runtime.language} extractor script is missing: {script_path}")
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
            raise RuntimeError(f"{runtime.language} extractor failed with exit code {completed.returncode}: {message}")
        extracted = self._parse_batch_output(request, completed.stdout)
        source_paths_by_id = {
            self.code.file_id(str(root), str(source_path)): source_path for source_path in source_paths
        }
        extracted_files: dict[FileId, SourceFile] = {}
        for raw_file_id, source_file in extracted.items():
            file_id = FileId(raw_file_id)
            source_path = source_paths_by_id[file_id]
            extracted_files[file_id] = SourceFile.model_validate(
                {
                    **source_file,
                    "file_id": file_id,
                    "module_id": self.code.module_id(str(root), str(source_path)),
                }
            )
        return extracted_files

    def _merge_files(self, files: dict[FileId, SourceFile], extracted: dict[FileId, SourceFile]) -> None:
        for file_id, source_file in extracted.items():
            if file_id in files:
                raise DuplicateIdentityError("file", file_id, file_id, file_id)
            files[file_id] = source_file

    def _parse_batch_output(self, request: ExtractionRequest, output: str) -> dict[str, Any]:
        if request.batch_config.output_format == "jsonl":
            result: dict[str, Any] = {}
            for line in output.splitlines():
                if not line.strip():
                    continue
                item: Any = json.loads(line)
                if not isinstance(item, list):
                    raise RuntimeError("Extractor returned invalid JSONL batch output.")
                item_list = cast(list[Any], item)
                if len(item_list) != 2:
                    raise RuntimeError("Extractor returned invalid JSONL batch output.")
                source_id, source_file = item_list
                if not isinstance(source_id, str):
                    raise RuntimeError("Extractor returned a non-string source id.")
                result[source_id] = source_file
            return result
        parsed: Any = json.loads(output)
        if not isinstance(parsed, dict):
            raise RuntimeError("Extractor returned invalid JSON batch output.")
        return cast(dict[str, Any], parsed)

    def _source_id_for_path(self, request: ExtractionRequest, root: Path, path: Path) -> FileId:
        return self.code.file_id(str(root), str(path))
