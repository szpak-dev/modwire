from pydantic import Field

from ...values.models.value_model import ValueModel


class ExtractorDescriptor(ValueModel):
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    language: str = Field(min_length=1)
    runtime: str = Field(min_length=1)
