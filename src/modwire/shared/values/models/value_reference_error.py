from ...failures.models.modwire_error import ModwireError
from ...failures.models.modwire_error_code import ModwireErrorCode
from .value_reference_violation import ValueReferenceViolation


class ValueReferenceError(ModwireError, ValueError):
    code = ModwireErrorCode.VALUE_REFERENCE

    def __init__(self, violation: ValueReferenceViolation, index: int) -> None:
        self.violation = violation
        self.index = index
        super().__init__(f"Value reference {index} violates {violation}.")
