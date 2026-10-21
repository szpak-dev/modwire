from .architecture_shape_error import ArchitectureShapeError
from .architecture_shape_violation import ArchitectureShapeViolation


class ArchitectureShapeValidationError(ArchitectureShapeError):
    code = "architecture_shape_validation"

    def __init__(self, violation: ArchitectureShapeViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Architecture shape violates {violation}: {subject}.")
