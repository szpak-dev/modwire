from typing import Literal, Self

from pydantic import model_validator

from ....values.models.value_model import ValueModel
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .inventory_location_kind import InventoryLocationKind


class InventorySourceLocation(ValueModel):
    kind: Literal[InventoryLocationKind.SOURCE] = InventoryLocationKind.SOURCE
    start_line: int
    end_line: int

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.start_line < 1 or self.end_line < self.start_line:
            raise CodeValidationError(
                CodeViolation.INVALID_INVENTORY_SOURCE_RANGE, f"{self.start_line}:{self.end_line}"
            )
        return self
