from typing import Literal

from pydantic import ConfigDict, Field

from ....shared.values.models.value_model import ValueModel


class ExtractorFailureDocument(ValueModel):
    """The strict failure document emitted by native extractor entrypoints."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, validate_default=True)
    code: Literal["source_parse"]
    language: str = Field(min_length=1)
    path: str = Field(min_length=1)
    line: int = Field(ge=1)
    column: int = Field(ge=1)
    diagnostic: str = Field(min_length=1)
