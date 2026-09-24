from ....shared.values.models.value_model import ValueModel
from ...pipeline.models.source_inventory import SourceInventory
from .cache_key import CacheKey
from .source_cache_entry import SourceCacheEntry


class CachePlan(ValueModel):
    inventory: SourceInventory
    sources: tuple[SourceCacheEntry, ...]
    manifest: CacheKey

    def manifest_value(self) -> dict[str, object]:
        return {
            "sources": [
                {
                    "relative_path": source.entry.relative_path,
                    "content_digest": source.entry.content_digest,
                    "source_key": source.key.digest,
                }
                for source in sorted(self.sources, key=lambda item: item.entry.relative_path)
            ]
        }
