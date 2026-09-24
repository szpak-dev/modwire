import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import metadata, resources
from typing import Any, ClassVar

from wireup import injectable

from ....architecture.config.models.architecture_config import ArchitectureConfig
from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....shared.code.models.code_map import CodeMap
from ...cache.models.cache_key import CacheKey, CacheKind
from ...cache.models.source_cache_entry import SourceCacheEntry
from ...pipeline.models.scan_policy import ScanPolicy
from ...pipeline.models.source_entry import SourceEntry


@injectable
@dataclass(frozen=True)
class CacheIdentity:
    SOURCE_VERSION: ClassVar[int] = 1
    MANIFEST_VERSION: ClassVar[int] = 1
    CODE_MAP_VERSION: ClassVar[int] = 1
    REPORT_VERSION: ClassVar[int] = 1

    def source(self, request: ExtractionRequest, policy: ScanPolicy, entry: SourceEntry) -> CacheKey:
        return self._key(
            "source",
            {
                "version": self.SOURCE_VERSION,
                "package": self._package_version(),
                "runtime": self._runtime_identity(request),
                "scan_policy": policy.model_dump(mode="json"),
                "relative_path": entry.relative_path,
                "source_id": entry.source_id,
                "content_digest": entry.content_digest,
            },
        )

    def manifest(
        self, request: ExtractionRequest, policy: ScanPolicy, sources: tuple[SourceCacheEntry, ...]
    ) -> CacheKey:
        manifest_sources = tuple(
            {
                "relative_path": source.entry.relative_path,
                "content_digest": source.entry.content_digest,
                "source_key": source.key.digest,
            }
            for source in sorted(sources, key=lambda item: item.entry.relative_path)
        )
        return self._key(
            "manifest",
            {
                "version": self.MANIFEST_VERSION,
                "package": self._package_version(),
                "runtime": self._runtime_identity(request),
                "scan_policy": policy.model_dump(mode="json"),
                "sources": manifest_sources,
            },
        )

    def code_map(self, language: str, manifest: CacheKey) -> CacheKey:
        return self._key(
            "code-map",
            {
                "version": self.CODE_MAP_VERSION,
                "package": self._package_version(),
                "code_map_schema": CodeMap.schema_version,
                "language": language,
                "manifest": manifest.model_dump(mode="json"),
            },
        )

    def reports(self, code_map: CodeMap, config: ArchitectureConfig) -> CacheKey:
        return self._key(
            "reports",
            {
                "version": self.REPORT_VERSION,
                "package": self._package_version(),
                "code_map": code_map.model_dump(mode="json"),
                "configuration": config.model_dump(mode="json"),
            },
        )

    def _runtime_identity(self, request: ExtractionRequest) -> dict[str, object]:
        runtime = request.runtime
        return {
            "runtime": runtime.model_dump(mode="json"),
            "batch": request.batch_config.model_dump(mode="json"),
            "resource_digest": self._resource_digest(runtime.resource.package, runtime.resource.path),
        }

    @lru_cache(maxsize=32)
    def _resource_digest(self, package: str, path: str) -> str:
        resource = resources.files(package).joinpath(path)
        return hashlib.sha256(resource.read_bytes()).hexdigest()

    @lru_cache(maxsize=1)
    def _package_version(self) -> str:
        try:
            return metadata.version("modwire")
        except metadata.PackageNotFoundError:
            return "0+unknown"

    def _key(self, kind: CacheKind, value: object) -> CacheKey:
        payload: Any = value
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        return CacheKey(kind=kind, digest=hashlib.sha256(serialized).hexdigest())
