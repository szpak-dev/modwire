from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .cache_error import CacheError
from .cache_violation import CacheViolation


class CacheValidationError(CacheError):
    code = ModwireErrorCode.CACHE_VALIDATION

    def __init__(self, violation: CacheViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Cache contract violates {violation}: {subject}.")
