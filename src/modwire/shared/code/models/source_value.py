from ...values.models.value_model import ValueModel
from .source_value_scope import SourceValueScope
from .types import SourceValueDeclarationKind, SourceValueKind, SourceVisibility


class SourceValue(ValueModel):
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declaration_kind: SourceValueDeclarationKind
    value_kind: SourceValueKind
    scope: SourceValueScope
    declared_args: int = 0
    optional_args: int = 0
