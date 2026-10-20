from pydantic import field_validator

from ....shared.values.models.value_model import ValueModel
from .cache_validation_error import CacheValidationError
from .cache_violation import CacheViolation


class CacheOptions(ValueModel):
    """Generic persistent-cache settings supplied by a caller."""

    directory: str
    namespace: str
    max_bytes: int

    @field_validator("directory", "namespace")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise CacheValidationError(CacheViolation.EMPTY_CACHE_LOCATION, value)
        return value

    @field_validator("max_bytes")
    @classmethod
    def _positive_size(cls, value: int) -> int:
        if value < 1:
            raise CacheValidationError(CacheViolation.INVALID_CACHE_CAPACITY, str(value))
        return value
