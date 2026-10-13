from .cache_error import CacheError


class CacheOwnershipError(CacheError):
    """Report a cache path that cannot be safely used by Modwire."""

    code = "cache_ownership"

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Cache ownership rejected for {path}: {reason}")
