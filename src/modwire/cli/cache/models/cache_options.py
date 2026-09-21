from pydantic import field_validator

from ....shared.values.models.value_model import ValueModel


class CacheOptions(ValueModel):
    """Generic persistent-cache settings supplied by a caller."""

    directory: str
    namespace: str
    max_bytes: int

    @field_validator("directory", "namespace")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Cache directory and namespace must not be empty.")
        return value

    @field_validator("max_bytes")
    @classmethod
    def _positive_size(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Cache max_bytes must be at least one.")
        return value
