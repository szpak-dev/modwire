from typing import Self

from pydantic import model_validator

from ..code_validation_error import CodeValidationError
from ..code_violation import CodeViolation
from .source_callable import SourceCallable
from .source_callable_kind import SourceCallableKind


class SourceAnonymousCallable(SourceCallable):
    kind: SourceCallableKind = SourceCallableKind.ANONYMOUS

    @model_validator(mode="after")
    def validate_kind(self) -> Self:
        if self.kind is not SourceCallableKind.ANONYMOUS:
            raise CodeValidationError(CodeViolation.INCONSISTENT_CALLABLE_KIND, self.qualified_name)
        return self
