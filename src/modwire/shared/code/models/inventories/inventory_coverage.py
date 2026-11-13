from typing import Self

from pydantic import model_validator

from ....values.models.value_model import ValueModel
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from .inventory_limitation import InventoryLimitation
from .inventory_status import InventoryStatus


class InventoryCoverage(ValueModel):
    status: InventoryStatus
    limitations: tuple[InventoryLimitation, ...]

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        requires_limitations = self.status in {
            InventoryStatus.INCOMPLETE,
            InventoryStatus.UNSUPPORTED,
            InventoryStatus.UNOBSERVED,
        }
        if requires_limitations != bool(self.limitations):
            raise CodeValidationError(CodeViolation.INVALID_INVENTORY_STATE, self.status.value)
        return self

    def validate_item_count(self, count: int) -> None:
        if count and self.status in {
            InventoryStatus.UNSUPPORTED,
            InventoryStatus.UNOBSERVED,
            InventoryStatus.NOT_APPLICABLE,
        }:
            raise CodeValidationError(CodeViolation.INVALID_INVENTORY_ITEM_COUNT, self.status.value)
