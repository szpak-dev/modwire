from typing import Self

from pydantic import model_validator

from ...values.models.value_model import ValueModel
from .declaration_family import DeclarationFamily
from .declaration_identity import DeclarationIdentity
from .source_symbol_kind import SourceSymbolKind
from .source_value_declaration_kind import SourceValueDeclarationKind
from .source_value_scope import SourceValueScope
from .source_visibility import SourceVisibility


class SourceValue(ValueModel):
    declaration_id: DeclarationIdentity
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declaration_kind: SourceValueDeclarationKind
    value_kind: SourceSymbolKind
    scope: SourceValueScope
    declared_args: int = 0
    optional_args: int = 0

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        value_kinds = {
            SourceSymbolKind.VALUE_CALLABLE,
            SourceSymbolKind.VALUE_CLASS,
            SourceSymbolKind.VALUE_LITERAL,
            SourceSymbolKind.VALUE_OBJECT,
            SourceSymbolKind.VALUE_UNKNOWN,
        }
        if self.declaration_id.family is not DeclarationFamily.VALUE or self.value_kind not in value_kinds:
            raise ValueError("Source value kind and identity family must describe a value.")
        return self
