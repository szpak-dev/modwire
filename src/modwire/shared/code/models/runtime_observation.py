from pydantic import Field

from ...values.models.value_model import ValueModel


class RuntimeObservation(ValueModel):
    version: str = Field(min_length=1)
    resource_digest: str = Field(pattern="^[0-9a-f]{64}$")
