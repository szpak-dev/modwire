from typing import Self

from pydantic import model_validator

from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..immutable_code_value import ImmutableCodeValue
from .inventory_limitation import InventoryLimitation
from .inventory_status import InventoryStatus


class InventoryCoverage(ImmutableCodeValue):
    status: InventoryStatus
    limitations: tuple[InventoryLimitation, ...]

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        requires_limitations = (
            self.status is InventoryStatus.INCOMPLETE
            or self.status is InventoryStatus.UNSUPPORTED
            or self.status is InventoryStatus.UNOBSERVED
        )
        if requires_limitations != bool(self.limitations):
            raise CodeValidationError(CodeViolation.INVALID_INVENTORY_STATE, self.status.value)
        return self

    def validate_item_count(self, count: int) -> None:
        if count and (
            self.status is InventoryStatus.UNSUPPORTED
            or self.status is InventoryStatus.UNOBSERVED
            or self.status is InventoryStatus.NOT_APPLICABLE
        ):
            raise CodeValidationError(CodeViolation.INVALID_INVENTORY_ITEM_COUNT, self.status.value)
