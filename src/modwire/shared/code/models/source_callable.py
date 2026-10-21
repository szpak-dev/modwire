from typing import Self

from pydantic import Field, model_validator

from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation
from .declaration_family import DeclarationFamily
from .declaration_identity import DeclarationIdentity
from .identity import FileId
from .source_callable_kind import SourceCallableKind
from .source_callable_symbol import SourceCallableSymbol
from .source_parameter import SourceParameter


class SourceCallable(SourceCallableSymbol):
    declaration_id: DeclarationIdentity
    source_id: FileId
    qualified_name: str
    owner_name: str = ""
    kind: SourceCallableKind
    line_start: int
    line_end: int
    parameters: list[SourceParameter] = Field(default_factory=list[SourceParameter])
    declared_args: int = 0
    optional_args: int = 0
    return_annotation: str = ""
    decorators: list[str] = Field(default_factory=list[str])
    docstring: str = ""

    @model_validator(mode="after")
    def validate_declaration_identity(self) -> Self:
        if self.declaration_id.source_id != self.source_id:
            raise CodeValidationError(CodeViolation.FOREIGN_CALLABLE_DECLARATION, self.qualified_name)
        if self.declaration_id.qualified_name != self.qualified_name:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_NAME, self.qualified_name)
        families = {
            SourceCallableKind.FUNCTION: DeclarationFamily.FUNCTION,
            SourceCallableKind.INSTANCE_METHOD: DeclarationFamily.METHOD,
            SourceCallableKind.TYPE_METHOD: DeclarationFamily.METHOD,
            SourceCallableKind.STATIC_METHOD: DeclarationFamily.METHOD,
            SourceCallableKind.CONSTRUCTOR: DeclarationFamily.METHOD,
            SourceCallableKind.CALLABLE_VALUE: DeclarationFamily.VALUE,
            SourceCallableKind.ANONYMOUS: DeclarationFamily.CALLABLE,
        }
        if self.declaration_id.family is not families[self.kind]:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_FAMILY, self.qualified_name)
        return self
