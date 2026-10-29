from typing import Self

from pydantic import model_validator

from ....values.models.value_model import ValueModel
from ..declarations.declaration_family import DeclarationFamily
from ..declarations.declaration_identity import DeclarationIdentity
from ..declarations.source_symbol_kind import SourceSymbolKind
from ..declarations.source_visibility import SourceVisibility
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .source_value_declaration_kind import SourceValueDeclarationKind
from .source_value_scope import SourceValueScope


class SourceValue(ValueModel):
    declaration_id: DeclarationIdentity
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declaration_kind: SourceValueDeclarationKind
    value_kind: SourceSymbolKind
    scope: SourceValueScope

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
            raise CodeValidationError(CodeViolation.INCONSISTENT_VALUE_IDENTITY_FAMILY, self.name)
        return self
