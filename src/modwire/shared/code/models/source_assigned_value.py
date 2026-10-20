from typing import Self

from pydantic import model_validator

from ...values.models.value_model import ValueModel
from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation
from .source_assigned_value_kind import SourceAssignedValueKind


class SourceAssignedValue(ValueModel):
    """Language-neutral evidence observed at one class-property assignment site."""

    kind: SourceAssignedValueKind
    expression: str
    reference: str

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Require the expression and reference fields appropriate to the evidence kind."""

        if self.kind in (SourceAssignedValueKind.UNASSIGNED, SourceAssignedValueKind.UNSUPPORTED):
            if self.expression or self.reference:
                raise CodeValidationError(CodeViolation.UNSUPPORTED_ASSIGNED_VALUE_EVIDENCE, self.kind)
        elif self.kind in (SourceAssignedValueKind.CALL, SourceAssignedValueKind.REFERENCE):
            if not self.expression or not self.reference:
                raise CodeValidationError(CodeViolation.INCOMPLETE_REFERENCE_VALUE_EVIDENCE, self.kind)
        elif not self.expression or self.reference:
            raise CodeValidationError(CodeViolation.INCONSISTENT_NON_REFERENCE_VALUE_EVIDENCE, self.kind)
        return self
