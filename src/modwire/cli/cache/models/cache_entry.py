from ....shared.values.models.value_model import ValueModel
from .cache_key import CacheKey


class CacheEntry(ValueModel):
    key: CacheKey
    size: int
    last_access_ns: int
