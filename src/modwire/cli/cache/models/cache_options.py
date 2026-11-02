from typing import Self

from pydantic import model_validator

from ....shared.values.models.value_model import ValueModel
from .cache_validation_error import CacheValidationError
from .cache_violation import CacheViolation


class CacheOptions(ValueModel):
    """Generic persistent-cache settings supplied by a caller."""

    directory: str
    namespace: str
    max_bytes: int

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        for value in (self.directory, self.namespace):
            if not value.strip():
                raise CacheValidationError(CacheViolation.EMPTY_CACHE_LOCATION, value)
        if self.max_bytes < 1:
            raise CacheValidationError(CacheViolation.INVALID_CACHE_CAPACITY, str(self.max_bytes))
        return self
