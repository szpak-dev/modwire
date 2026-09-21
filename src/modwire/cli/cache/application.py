import importlib
from dataclasses import dataclass
from typing import Any, cast

from pydantic import BaseModel, ValidationError
from wireup import injectable

from ...architecture.config.models.architecture_config import ArchitectureConfig
from ...architecture.report.models.report_node import ReportNode
from ...extraction.extractors.models.extraction_request import ExtractionRequest
from ...shared.code.models.code_map import CodeMap
from ...shared.code.models.duplicate_identity_error import DuplicateIdentityError
from ...shared.code.models.identity import FileId, ModuleId
from ...shared.code.models.source_extraction import SourceExtraction
from ...shared.code.models.source_file import SourceFile
from ..pipeline.domain import SourceReader
from ..pipeline.models.scan_policy import ScanPolicy
from .domain import CacheStorage
from .models.cache_key import CacheKey
from .models.cache_options import CacheOptions
from .models.extraction_snapshot import ExtractionSnapshot
from .services.cache_codec import CacheCodec
from .services.cache_identity import CacheIdentity


@injectable
@dataclass(frozen=True)
class CacheApplication:
    reader: SourceReader
    storage: CacheStorage
    identity: CacheIdentity
    codec: CacheCodec

    def has_source_files(self, request: ExtractionRequest, policy: ScanPolicy) -> bool:
        return self.reader.has_source_files(request, policy)

    def extract(self, request: ExtractionRequest, policy: ScanPolicy) -> SourceExtraction:
        self.reader.ensure_available(request.runtime)
        return self.reader.extract_source(request, policy)

    def extract_cached(
        self, request: ExtractionRequest, policy: ScanPolicy, options: CacheOptions
    ) -> ExtractionSnapshot:
        inventory = self.reader.inventory(request, policy)
        keys = {entry.source_id: self.identity.source(request, policy, entry) for entry in inventory.entries}
        files: dict[FileId, SourceFile] = {}
        misses: list[FileId] = []
        for entry in inventory.entries:
            key = keys[entry.source_id]
            value = self._read(options, key)
            try:
                source_file = SourceFile.model_validate(value)
                if source_file.file_id != entry.source_id:
                    raise ValueError("Cached source identity does not match its key.")
                files[entry.source_id] = source_file
            except (TypeError, ValueError, ValidationError):
                self.storage.delete(options, key)
                misses.append(entry.source_id)

        if misses or not inventory.entries:
            self.reader.ensure_available(request.runtime)
        extracted = self.reader.extract_entries(request, inventory, tuple(misses))
        for source_id in misses:
            source_file = extracted.get(source_id)
            if source_file is None:
                raise RuntimeError(f"Extractor omitted a requested source file: {source_id}")
            files[source_id] = source_file
            self._write(options, keys[source_id], source_file.model_dump(mode="json"))

        ordered_files = {entry.source_id: files[entry.source_id] for entry in inventory.entries}
        modules: dict[ModuleId, FileId] = {}
        for file_id, source_file in ordered_files.items():
            existing = modules.get(source_file.module_id)
            if existing is not None:
                raise DuplicateIdentityError("module", source_file.module_id, existing, file_id)
            modules[source_file.module_id] = file_id

        extraction = SourceExtraction(
            files=ordered_files,
            modules=modules,
            files_found=inventory.files_found,
            files_excluded=inventory.files_excluded,
            directories_pruned=inventory.directories_pruned,
        )
        manifest = self.identity.manifest(request, policy, inventory.entries)
        self._write(
            options,
            manifest,
            {
                "sources": [
                    {
                        "relative_path": entry.relative_path,
                        "content_digest": entry.content_digest,
                        "source_key": keys[entry.source_id].digest,
                    }
                    for entry in inventory.entries
                ]
            },
        )
        self.prune(options)
        return ExtractionSnapshot(extraction=extraction, manifest=manifest)

    def code_map(self, snapshot: ExtractionSnapshot, options: CacheOptions) -> CodeMap | None:
        key = self.identity.code_map("", snapshot.manifest)
        value = self._read(options, key)
        try:
            return CodeMap.model_validate(value)
        except (TypeError, ValueError, ValidationError):
            self.storage.delete(options, key)
            return None

    def store_code_map(self, snapshot: ExtractionSnapshot, code_map: CodeMap, options: CacheOptions) -> None:
        self._write(options, self.identity.code_map("", snapshot.manifest), code_map.model_dump(mode="json"))
        self.prune(options)

    def reports(
        self, code_map: CodeMap, config: ArchitectureConfig, options: CacheOptions
    ) -> tuple[ReportNode, ...] | None:
        key = self.identity.reports(code_map, config)
        value = self._read(options, key)
        try:
            if not isinstance(value, list):
                raise ValueError("Cached reports must be a list.")
            reports = tuple(self._report(item) for item in cast(list[object], value))
            return tuple(sorted(reports, key=lambda item: (item.metadata.order, item.metadata.id)))
        except (AttributeError, ImportError, KeyError, TypeError, ValueError, ValidationError):
            self.storage.delete(options, key)
            return None

    def store_reports(
        self,
        code_map: CodeMap,
        config: ArchitectureConfig,
        reports: tuple[ReportNode, ...],
        options: CacheOptions,
    ) -> None:
        value = [
            {
                "model": f"{type(report).__module__}.{type(report).__qualname__}",
                "payload": report.model_dump(mode="json", exclude_computed_fields=True),
            }
            for report in reports
        ]
        self._write(options, self.identity.reports(code_map, config), value)
        self.prune(options)

    def clear(self, options: CacheOptions) -> None:
        self.storage.clear(options)

    def prune(self, options: CacheOptions) -> None:
        entries = self.storage.entries(options)
        total = sum(entry.size for entry in entries)
        for entry in sorted(entries, key=lambda item: (item.last_access_ns, item.key.kind, item.key.digest)):
            if total <= options.max_bytes:
                break
            self.storage.delete(options, entry.key)
            total -= entry.size

    def _read(self, options: CacheOptions, key: CacheKey) -> object | None:
        payload = self.storage.read(options, key)
        if payload is None:
            return None
        value = self.codec.decode(key, payload)
        if value is None:
            self.storage.delete(options, key)
        return value

    def _write(self, options: CacheOptions, key: CacheKey, value: object) -> None:
        self.storage.write(options, key, self.codec.encode(key, value))

    def _report(self, value: object) -> ReportNode:
        if not isinstance(value, dict):
            raise ValueError("Cached report entry must be an object.")
        entry = cast(dict[str, object], value)
        model_name = entry["model"]
        payload = entry["payload"]
        if not isinstance(model_name, str) or not model_name.startswith("modwire.architecture."):
            raise ValueError("Cached report model is outside the architecture package.")
        module_name, _, class_name = model_name.rpartition(".")
        model: Any = getattr(importlib.import_module(module_name), class_name)
        if not isinstance(model, type) or not issubclass(model, BaseModel) or not issubclass(model, ReportNode):
            raise ValueError("Cached report model is not a report node.")
        return model.model_validate(payload)
