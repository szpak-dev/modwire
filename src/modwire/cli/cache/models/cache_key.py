from typing import Literal

from ....shared.values.models.value_model import ValueModel

type CacheKind = Literal["source", "manifest", "code-map", "reports"]


class CacheKey(ValueModel):
    schema_version: Literal[1] = 1
    kind: CacheKind
    digest: str
