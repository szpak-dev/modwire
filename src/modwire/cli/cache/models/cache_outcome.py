from pydantic import field_validator

from ....shared.values.models.value_model import ValueModel
from .cache_stage import CacheStage


class CacheOutcome(ValueModel):
    """Content-safe lifecycle counts for one stage of a cached operation.

    Extraction counts describe current source records. An exact code-map hit
    reports its digest-backed manifest sources as extraction hits without loading
    individual source payloads. Code-map and report counts describe one entry.
    Invalidated entries are also misses. Diagnostics include the configured
    namespace but never cache keys, source identities, or content.
    """

    stage: CacheStage
    namespace: str
    hits: int = 0
    misses: int = 0
    invalidated: int = 0
    computed: int = 0
    stored: int = 0

    @field_validator("namespace")
    @classmethod
    def _non_empty_namespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Cache outcome namespace must not be empty.")
        return value

    @field_validator("hits", "misses", "invalidated", "computed", "stored")
    @classmethod
    def _non_negative_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Cache outcome counts must not be negative.")
        return value
