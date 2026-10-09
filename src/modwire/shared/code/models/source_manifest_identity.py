from pydantic import Field

from ...values.models.value_model import ValueModel
from .digest_algorithm import DigestAlgorithm


class SourceManifestIdentity(ValueModel):
    """Canonical identity of one observed source manifest."""

    digest_algorithm: DigestAlgorithm
    digest: str = Field(pattern="^[0-9a-f]{64}$")
