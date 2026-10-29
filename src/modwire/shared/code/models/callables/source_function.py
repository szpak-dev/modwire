from typing import Self

from pydantic import model_validator

from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .source_callable import SourceCallable
from .source_callable_kind import SourceCallableKind


class SourceFunction(SourceCallable):
    kind: SourceCallableKind = SourceCallableKind.FUNCTION

    @model_validator(mode="after")
    def validate_kind(self) -> Self:
        if self.kind is not SourceCallableKind.FUNCTION:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_KIND, self.qualified_name)
        return self
