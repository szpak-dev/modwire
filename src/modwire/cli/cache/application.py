import importlib
from dataclasses import dataclass
from typing import Any, cast

from pydantic import BaseModel, ValidationError
from wireup import injectable

from ...architecture.config.models.architecture_config import ArchitectureConfig
from ...architecture.report.models.report_node import ReportNode
from ...extraction.extractors.models.duplicate_identity_error import DuplicateIdentityError
from ...extraction.extractors.models.extraction_request import ExtractionRequest
from ...shared.code.models.code_error import CodeError
from ...shared.code.models.code_map import CodeMap
from ...shared.code.models.identity import FileId, ImportIdentity
from ...shared.code.models.identity_kind import IdentityKind
from ...shared.code.models.scan_policy import ScanPolicy
from ...shared.code.models.source_extraction import SourceExtraction
from ...shared.code.models.source_file import SourceFile
from ..pipeline.domain import SourceReader
from ..pipeline.models.source_observation import SourceObservation
from .domain import CacheStorage
from .models.cache_key import CacheKey
from .models.cache_options import CacheOptions
from .models.cache_outcome import CacheOutcome
from .models.cache_plan import CachePlan
from .models.cache_stage import CacheStage
from .models.cache_validation_error import CacheValidationError
from .models.cache_violation import CacheViolation
from .models.cached_result import CachedResult
from .models.source_cache_entry import SourceCacheEntry
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

    def prepare(self, observation: SourceObservation) -> CachePlan:
        request = observation.request
        policy = observation.manifest.policy
        sources = tuple(
            SourceCacheEntry(
                entry=entry,
                key=self.identity.source(request, policy, observation.manifest.runtime, entry),
            )
            for entry in observation.entries
        )
        return CachePlan(
            language=request.runtime.descriptor.language,
            observation=observation,
            sources=sources,
            source_set=self.identity.source_set(request, observation.manifest, sources),
        )

    def sources(self, plan: CachePlan, options: CacheOptions) -> CachedResult[SourceExtraction]:
        observation = plan.observation
        request = observation.request
        payloads = self.storage.read_many(options, tuple(source.key for source in plan.sources))
        files: dict[FileId, SourceFile] = {}
        misses: list[FileId] = []
        invalid_keys: list[CacheKey] = []
        hits = 0
        invalidated = 0
        sources_by_id = {source.entry.source_id: source for source in plan.sources}
        for source, payload in zip(plan.sources, payloads, strict=True):
            cached_value = self.codec.decode(source.key, payload) if payload is not None else None
            cached_invalidated = payload is not None and cached_value is None
            try:
                source_file = SourceFile.model_validate(cached_value)
                if source_file.file_id != source.entry.source_id:
                    raise CacheValidationError(CacheViolation.SOURCE_IDENTITY_MISMATCH, str(source.key))
                files[source.entry.source_id] = source_file
                hits += 1
            except (CacheValidationError, CodeError, TypeError, ValueError, ValidationError):
                if payload is not None:
                    invalid_keys.append(source.key)
                invalidated += int(cached_invalidated or cached_value is not None)
                misses.append(source.entry.source_id)
        self.storage.delete_many(options, tuple(invalid_keys))

        if misses or not observation.entries:
            self.reader.ensure_available(request.runtime)
        extracted = self.reader.extract_entries(observation, tuple(misses))
        writes: list[tuple[CacheKey, bytes]] = []
        for source_id in misses:
            source_file = extracted[source_id]
            files[source_id] = source_file
            source = sources_by_id[source_id]
            writes.append((source.key, self.codec.encode(source.key, source_file.model_dump(mode="json"))))
        self.storage.write_many(options, tuple(writes))

        ordered_files = {source.entry.source_id: files[source.entry.source_id] for source in plan.sources}
        import_identities: dict[ImportIdentity, FileId] = {}
        for file_id, source_file in ordered_files.items():
            existing = import_identities.get(source_file.import_identity)
            if existing is not None:
                raise DuplicateIdentityError(IdentityKind.IMPORT, source_file.import_identity, existing, file_id)
            import_identities[source_file.import_identity] = file_id

        extraction = SourceExtraction(
            files=ordered_files,
            import_identities=import_identities,
            manifest=observation.manifest,
            files_found=observation.files_found,
            files_excluded=observation.files_excluded,
            directories_pruned=observation.directories_pruned,
        )
        return CachedResult(
            value=extraction,
            outcomes=(
                CacheOutcome(
                    stage=CacheStage.EXTRACTION,
                    namespace=options.namespace,
                    hits=hits,
                    misses=len(misses),
                    invalidated=invalidated,
                    computed=len(misses),
                    stored=len(misses),
                ),
            ),
        )

    def maintain_source_set(self, plan: CachePlan, options: CacheOptions) -> bool:
        expected = plan.source_set_value()
        payload = self.storage.read(options, plan.source_set)
        if payload is not None and self.codec.decode(plan.source_set, payload) == expected:
            return False
        return self._write(options, plan.source_set, expected)

    def code_map(self, plan: CachePlan, options: CacheOptions) -> CachedResult[CodeMap | None]:
        key = self.identity.code_map(plan.language, plan.source_set)
        cached_value, cached_invalidated = self._read(options, key)
        try:
            value = CodeMap.model_validate(cached_value)
            if value.extraction.manifest != plan.observation.manifest:
                raise CacheValidationError(CacheViolation.CODE_MAP_PROVENANCE_MISMATCH, str(key))
            outcome = CacheOutcome(stage=CacheStage.CODE_MAP, namespace=options.namespace, hits=1)
        except (CacheValidationError, CodeError, TypeError, ValueError, ValidationError):
            if cached_value is not None and not cached_invalidated:
                self.storage.delete(options, key)
            value = None
            outcome = CacheOutcome(
                stage=CacheStage.CODE_MAP,
                namespace=options.namespace,
                misses=1,
                invalidated=int(cached_invalidated or cached_value is not None),
            )
        return CachedResult[CodeMap | None](value=value, outcomes=(outcome,))

    def store_code_map(self, plan: CachePlan, code_map: CodeMap, options: CacheOptions) -> None:
        self._write(
            options,
            self.identity.code_map(plan.language, plan.source_set),
            code_map.model_dump(mode="json"),
        )

    def reports(
        self, code_map: CodeMap, config: ArchitectureConfig, options: CacheOptions
    ) -> CachedResult[tuple[ReportNode, ...] | None]:
        key = self.identity.reports(code_map, config)
        cached_value, cached_invalidated = self._read(options, key)
        invalidated = cached_invalidated or cached_value is not None
        try:
            if not isinstance(cached_value, list):
                raise CacheValidationError(CacheViolation.REPORT_COLLECTION_INVALID, str(key))
            reports = tuple(self._report(item) for item in cast(list[object], cached_value))
            value = tuple(sorted(reports, key=lambda item: (item.metadata.order, item.metadata.id)))
            outcome = CacheOutcome(stage=CacheStage.REPORTS, namespace=options.namespace, hits=1)
        except (AttributeError, CacheValidationError, ImportError, KeyError, TypeError, ValueError, ValidationError):
            if cached_value is not None and not cached_invalidated:
                self.storage.delete(options, key)
            value = None
            outcome = CacheOutcome(
                stage=CacheStage.REPORTS,
                namespace=options.namespace,
                misses=1,
                invalidated=int(invalidated),
            )
        return CachedResult[tuple[ReportNode, ...] | None](value=value, outcomes=(outcome,))

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

    def maintain(self, options: CacheOptions) -> bool:
        return self.storage.enforce_capacity(options)

    def clear(self, options: CacheOptions) -> None:
        self.storage.clear(options)

    def _read(self, options: CacheOptions, key: CacheKey) -> tuple[object | None, bool]:
        payload = self.storage.read(options, key)
        if payload is None:
            return None, False
        value = self.codec.decode(key, payload)
        if value is None:
            self.storage.delete(options, key)
            return None, True
        return value, False

    def _write(self, options: CacheOptions, key: CacheKey, value: object) -> bool:
        return self.storage.write(options, key, self.codec.encode(key, value))

    def _report(self, value: object) -> ReportNode:
        if not isinstance(value, dict):
            raise CacheValidationError(CacheViolation.REPORT_ENTRY_INVALID, type(value).__name__)
        entry = cast(dict[str, object], value)
        model_name = entry["model"]
        payload = entry["payload"]
        if not isinstance(model_name, str) or not model_name.startswith("modwire.architecture."):
            raise CacheValidationError(CacheViolation.REPORT_MODEL_OUTSIDE_ARCHITECTURE, str(model_name))
        module_name, _, class_name = model_name.rpartition(".")
        model: Any = getattr(importlib.import_module(module_name), class_name)
        if not isinstance(model, type) or not issubclass(model, BaseModel) or not issubclass(model, ReportNode):
            raise CacheValidationError(CacheViolation.REPORT_MODEL_NOT_NODE, model_name)
        return model.model_validate(payload)
