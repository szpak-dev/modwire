from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .extractor_error import ExtractorError
from .extractor_invariant_violation import ExtractorInvariantViolation


class ExtractorInvariantError(ExtractorError):
    code = ModwireErrorCode.EXTRACTOR_INVARIANT

    def __init__(self, violation: ExtractorInvariantViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Extractor invariant violates {violation}: {subject}.")
