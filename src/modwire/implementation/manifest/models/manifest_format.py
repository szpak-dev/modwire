from pydantic import Field

from ....shared.values.models.value_model import ValueModel


class ManifestFormat(ValueModel):
    id: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
