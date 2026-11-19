from typing import Annotated, Self

from pydantic import model_validator
from pydantic.dataclasses import dataclass

from ....values.models.value_model import ValueModel
from ....values.models.value_reference import ValueReference
from ..declarations.declaration_family import DeclarationFamily
from ..declarations.declaration_identity import DeclarationIdentity
from ..declarations.source_placement import SourcePlacement
from ..declarations.source_symbol_kind import SourceSymbolKind
from ..declarations.source_visibility import SourceVisibility
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .source_value_declaration_kind import SourceValueDeclarationKind
from .source_value_scope import SourceValueScope


@dataclass(slots=True, kw_only=True, config=ValueModel.model_config)
class SourceValue:
    declaration_id: Annotated[DeclarationIdentity, ValueReference()]
    name: str
    visibility: SourceVisibility
    visibility_intent: SourceVisibility
    line_count: int
    declaration_kind: SourceValueDeclarationKind
    value_kind: SourceSymbolKind
    scope: SourceValueScope
    placement: Annotated[SourcePlacement, ValueReference()]

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.declaration_id.family is not DeclarationFamily.VALUE or not (
            self.value_kind is SourceSymbolKind.VALUE_CALLABLE
            or self.value_kind is SourceSymbolKind.VALUE_CLASS
            or self.value_kind is SourceSymbolKind.VALUE_LITERAL
            or self.value_kind is SourceSymbolKind.VALUE_OBJECT
            or self.value_kind is SourceSymbolKind.VALUE_UNKNOWN
        ):
            raise CodeValidationError(CodeViolation.INCONSISTENT_VALUE_IDENTITY_FAMILY, self.name)
        return self
