from ....shared.values.models.value_model import ValueModel
from ...pipeline.models.source_entry import SourceEntry
from .cache_key import CacheKey


class SourceCacheEntry(ValueModel):
    entry: SourceEntry
    key: CacheKey
