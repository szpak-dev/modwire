import hashlib
from typing import Self

from pydantic import Field, model_validator

from ....shared.values.models.value_model import ValueModel
from .digest_algorithm import DigestAlgorithm
from .manifest_format import ManifestFormat


class ImplementationManifestDocument(ValueModel):
    format: ManifestFormat
    payload: str = Field(min_length=1)
    algorithm: DigestAlgorithm
    digest: str = Field(pattern="^[0-9a-f]{64}$")

    def verify_digest(self) -> bool:
        """Return whether the payload matches the declared digest."""

        return hashlib.sha256(self.payload.encode("utf-8")).hexdigest() == self.digest

    @model_validator(mode="after")
    def validate_digest(self) -> Self:
        """Validate that the document digest covers its exact serialized payload."""

        if not self.verify_digest():
            raise ValueError("Implementation manifest document digest does not match its payload.")
        return self
