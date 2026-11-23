from typing import Annotated, Self

from pydantic import model_validator

from ....values.models.value_reference import ValueReference
from ..declarations.declaration_family import DeclarationFamily
from ..declarations.declaration_identity import DeclarationIdentity
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .source_callable import SourceCallable


class SourceClassMethod(SourceCallable):
    owner_declaration_id: Annotated[DeclarationIdentity, ValueReference()]

    @model_validator(mode="after")
    def validate_owner(self) -> Self:
        if self.kind.declaration_family is not DeclarationFamily.METHOD:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_KIND, self.qualified_name)
        if self.owner_declaration_id.source_id != self.source_id:
            raise CodeValidationError(CodeViolation.FOREIGN_MEMBER_OWNER, self.qualified_name)
        return self
