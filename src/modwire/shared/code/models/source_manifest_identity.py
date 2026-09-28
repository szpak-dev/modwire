from pydantic import Field

from ...values.models.value_model import ValueModel


class SourceManifestIdentity(ValueModel):
    """Canonical identity of one observed source manifest."""

    digest_algorithm: str = Field(pattern="^sha256$")
    digest: str = Field(pattern="^[0-9a-f]{64}$")
