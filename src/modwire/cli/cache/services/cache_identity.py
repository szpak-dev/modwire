import hashlib
import json
from dataclasses import dataclass
from typing import ClassVar

from wireup import injectable

from ....architecture.config.models.architecture_config import ArchitectureConfig
from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....shared.code.domain import PackageVersion
from ....shared.code.models.code_map import CodeMap
from ....shared.code.models.runtime_observation import RuntimeObservation
from ....shared.code.models.scan_policy import ScanPolicy
from ....shared.code.models.source_manifest import SourceManifest
from ...cache.models.cache_key import CacheKey
from ...cache.models.cache_kind import CacheKind
from ...cache.models.source_cache_entry import SourceCacheEntry
from ...pipeline.models.source_entry import SourceEntry


@injectable
@dataclass(frozen=True)
class CacheIdentity:
    version: PackageVersion

    SOURCE_VERSION: ClassVar[int] = 2
    SOURCE_SET_VERSION: ClassVar[int] = 3
    CODE_MAP_VERSION: ClassVar[int] = 2
    REPORT_VERSION: ClassVar[int] = 1

    def source(
        self,
        request: ExtractionRequest,
        policy: ScanPolicy,
        runtime: RuntimeObservation,
        entry: SourceEntry,
    ) -> CacheKey:
        return self.key(
            CacheKind.SOURCE,
            {
                "version": self.SOURCE_VERSION,
                "package": self.version.version(),
                "runtime": self.runtime_identity(request, runtime),
                "scan_policy": policy.model_dump(mode="json"),
                "relative_path": entry.relative_path,
                "source_id": entry.source_id,
                "content_digest": entry.content_digest,
            },
        )

    def source_set(
        self,
        request: ExtractionRequest,
        manifest: SourceManifest,
        sources: tuple[SourceCacheEntry, ...],
    ) -> CacheKey:
        source_set_entries = tuple(
            {
                "relative_path": source.entry.relative_path,
                "content_digest": source.entry.content_digest,
                "source_key": source.key.digest,
            }
            for source in sorted(sources, key=lambda item: item.entry.relative_path)
        )
        return self.key(
            CacheKind.SOURCE_SET,
            {
                "version": self.SOURCE_SET_VERSION,
                "package": self.version.version(),
                "runtime": self.runtime_identity(request, manifest.runtime),
                "source_manifest": manifest.digest,
                "sources": source_set_entries,
            },
        )

    def code_map(self, language: str, source_set: CacheKey) -> CacheKey:
        return self.key(
            CacheKind.CODE_MAP,
            {
                "version": self.CODE_MAP_VERSION,
                "package": self.version.version(),
                "code_map_schema": CodeMap.schema_version,
                "language": language,
                "source_set": source_set.model_dump(mode="json"),
            },
        )

    def reports(self, code_map: CodeMap, config: ArchitectureConfig) -> CacheKey:
        return self.key(
            CacheKind.REPORTS,
            {
                "version": self.REPORT_VERSION,
                "package": self.version.version(),
                "code_map": code_map.model_dump(mode="json"),
                "configuration": config.model_dump(mode="json"),
            },
        )

    def runtime_identity(self, request: ExtractionRequest, observation: RuntimeObservation) -> dict[str, object]:
        return {
            "runtime": request.runtime.model_dump(mode="json"),
            "batch": request.batch_config.model_dump(mode="json"),
            "observation": observation.model_dump(mode="json"),
        }

    def key(self, kind: CacheKind, value: object) -> CacheKey:
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        return CacheKey(kind=kind, digest=hashlib.sha256(serialized).hexdigest())
