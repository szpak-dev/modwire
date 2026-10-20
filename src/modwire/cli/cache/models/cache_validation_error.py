from .cache_error import CacheError
from .cache_violation import CacheViolation


class CacheValidationError(CacheError):
    code = "cache_validation"

    def __init__(self, violation: CacheViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Cache contract violates {violation}: {subject}.")
