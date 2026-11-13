from typing import Self

from pydantic import Field, model_validator

from ..declarations.source_unresolved_target import SourceUnresolvedTarget
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .source_callable import SourceCallable
from .source_callable_kind import SourceCallableKind


class SourceUnresolvedMethod(SourceCallable):
    receiver_reference: str = Field(min_length=1)
    owner: SourceUnresolvedTarget

    @model_validator(mode="after")
    def validate_kind(self) -> Self:
        if self.kind not in {
            SourceCallableKind.INSTANCE_METHOD,
            SourceCallableKind.TYPE_METHOD,
            SourceCallableKind.STATIC_METHOD,
            SourceCallableKind.CONSTRUCTOR,
        }:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_KIND, self.qualified_name)
        return self
