from typing import Self

from pydantic import model_validator

from ..code_validation_error import CodeValidationError
from ..code_violation import CodeViolation
from ..source_symbol_kind import SourceSymbolKind
from ..values.source_value_declaration_kind import SourceValueDeclarationKind
from ..values.source_value_scope import SourceValueScope
from .source_callable import SourceCallable
from .source_callable_kind import SourceCallableKind


class SourceCallableValue(SourceCallable):
    kind: SourceCallableKind = SourceCallableKind.CALLABLE_VALUE
    declaration_kind: SourceValueDeclarationKind
    value_kind: SourceSymbolKind = SourceSymbolKind.VALUE_CALLABLE
    scope: SourceValueScope

    @model_validator(mode="after")
    def validate_kind(self) -> Self:
        if self.kind is not SourceCallableKind.CALLABLE_VALUE:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_KIND, self.qualified_name)
        if self.value_kind is not SourceSymbolKind.VALUE_CALLABLE:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_KIND, self.qualified_name)
        return self
