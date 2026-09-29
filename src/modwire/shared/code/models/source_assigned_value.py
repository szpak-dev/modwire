from typing import Self

from pydantic import model_validator

from ...values.models.value_model import ValueModel
from .source_assigned_value_kind import SourceAssignedValueKind


class SourceAssignedValue(ValueModel):
    kind: SourceAssignedValueKind
    expression: str
    reference: str

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.kind in (SourceAssignedValueKind.UNASSIGNED, SourceAssignedValueKind.UNSUPPORTED):
            if self.expression or self.reference:
                raise ValueError("Unassigned and unsupported values cannot contain expression evidence.")
        elif self.kind in (SourceAssignedValueKind.CALL, SourceAssignedValueKind.REFERENCE):
            if not self.expression or not self.reference:
                raise ValueError("Call and reference values require an expression and exact reference.")
        elif not self.expression or self.reference:
            raise ValueError("Literal and unresolved values require an expression without a reference.")
        return self
