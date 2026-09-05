from modwire.shared.code.models.types import SourceValueDeclarationKind, SourceValueKind, SourceVisibility
from modwire.shared.values.models.value_model import ValueModel


class SourceValue(ValueModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declaration_kind: SourceValueDeclarationKind
    value_kind: SourceValueKind
    declared_args: int = 0
    optional_args: int = 0
