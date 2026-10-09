from typing import Self

from pydantic import Field, model_validator

from .declaration_family import DeclarationFamily
from .declaration_identity import DeclarationIdentity
from .identity import FileId
from .source_callable_kind import SourceCallableKind
from .source_callable_symbol import SourceCallableSymbol
from .source_parameter import SourceParameter


class SourceCallable(SourceCallableSymbol):
    declaration_id: DeclarationIdentity
    id: str
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
            raise ValueError("Callable declaration identity must reference its owning source file.")
        if self.declaration_id.qualified_name != self.qualified_name:
            raise ValueError("Callable declaration identity must match its qualified name.")
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
            raise ValueError("Callable declaration identity family must match its callable kind.")
        return self
