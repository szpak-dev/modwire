from typing import Annotated, Self

from pydantic import Field, model_validator

from ....values.models.string_reference import StringReference
from ....values.models.value_reference import ValueReference
from ..declarations.declaration_identity import DeclarationIdentity
from ..declarations.source_placement import SourcePlacement
from ..declarations.source_symbol import SourceSymbol
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..source_types.absent import SourceTypeAbsent
from ..source_types.reference import SourceTypeReference
from ..source_types.unsupported import SourceTypeUnsupported
from ..sources.identity import FileId
from .source_callable_kind import SourceCallableKind
from .source_parameter import SourceParameter


class SourceCallable(SourceSymbol):
    declaration_id: Annotated[DeclarationIdentity, ValueReference()]
    source_id: Annotated[FileId, StringReference()]
    qualified_name: str
    kind: SourceCallableKind
    placement: Annotated[SourcePlacement, ValueReference()]
    line_start: int
    line_end: int
    parameters: tuple[Annotated[SourceParameter, ValueReference()], ...] = Field(default_factory=tuple)
    return_type: Annotated[SourceTypeAbsent | SourceTypeReference | SourceTypeUnsupported, ValueReference()] = Field(
        union_mode="left_to_right"
    )
    decorators: tuple[str, ...] = Field(default_factory=tuple)
    docstring: str = ""

    @model_validator(mode="after")
    def validate_declaration_identity(self) -> Self:
        if self.declaration_id.source_id != self.source_id:
            raise CodeValidationError(CodeViolation.FOREIGN_CALLABLE_DECLARATION, self.qualified_name)
        if self.declaration_id.qualified_name != self.qualified_name:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_NAME, self.qualified_name)
        if self.declaration_id.family is not self.kind.declaration_family:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_FAMILY, self.qualified_name)
        return self
