from ...values.models.value_model import ValueModel
from .types import SourceVisibility


class SourceSymbol(ValueModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
