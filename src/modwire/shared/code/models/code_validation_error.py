from .code_error import CodeError
from .code_violation import CodeViolation


class CodeValidationError(CodeError):
    """Report shared code evidence that violates its typed contract."""

    code = "code_validation"

    def __init__(self, violation: CodeViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Code contract violates {violation}: {subject}.")
