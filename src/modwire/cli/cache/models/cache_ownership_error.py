from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .cache_error import CacheError


class CacheOwnershipError(CacheError):
    """Report a cache path that cannot be safely used by Modwire."""

    code = ModwireErrorCode.CACHE_OWNERSHIP

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Cache ownership rejected for {path}: {reason}")
