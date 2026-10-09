from ...values.models.value_model import ValueModel
from .declaration_identity import DeclarationIdentity
from .source_value_declaration_kind import SourceValueDeclarationKind
from .source_value_kind import SourceValueKind
from .source_value_scope import SourceValueScope
from .source_visibility import SourceVisibility


class SourceValue(ValueModel):
    declaration_id: DeclarationIdentity
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declaration_kind: SourceValueDeclarationKind
    value_kind: SourceValueKind
    scope: SourceValueScope
    declared_args: int = 0
    optional_args: int = 0
