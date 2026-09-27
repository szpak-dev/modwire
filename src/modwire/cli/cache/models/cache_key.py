from typing import Literal

from ....shared.values.models.value_model import ValueModel
from .cache_kind import CacheKind


class CacheKey(ValueModel):
    schema_version: Literal[1] = 1
    kind: CacheKind
    digest: str
