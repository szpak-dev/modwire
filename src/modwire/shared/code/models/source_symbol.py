from pydantic import Field

from ...values.models.value_model import ValueModel
from .types import SourceVisibility


class SourceSymbol(ValueModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declaration_annotations: list[str] = Field(default_factory=list[str])
