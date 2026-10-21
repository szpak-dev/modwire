from .architecture_config_error import ArchitectureConfigError
from .architecture_config_violation import ArchitectureConfigViolation


class ArchitectureConfigValidationError(ArchitectureConfigError):
    code = "architecture_config_validation"

    def __init__(self, violation: ArchitectureConfigViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Architecture configuration violates {violation}: {subject}.")
