from typing import Self

from pydantic import model_validator

from ..code_validation_error import CodeValidationError
from ..code_violation import CodeViolation
from ..declaration_identity import DeclarationIdentity
from .source_callable import SourceCallable
from .source_callable_kind import SourceCallableKind


class SourceClassMethod(SourceCallable):
    owner_declaration_id: DeclarationIdentity

    @model_validator(mode="after")
    def validate_owner(self) -> Self:
        if self.kind not in {
            SourceCallableKind.INSTANCE_METHOD,
            SourceCallableKind.TYPE_METHOD,
            SourceCallableKind.STATIC_METHOD,
            SourceCallableKind.CONSTRUCTOR,
        }:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_KIND, self.qualified_name)
        if self.owner_declaration_id.source_id != self.source_id:
            raise CodeValidationError(CodeViolation.FOREIGN_MEMBER_OWNER, self.qualified_name)
        return self
