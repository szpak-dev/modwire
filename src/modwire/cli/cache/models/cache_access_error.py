from .cache_error import CacheError


class CacheAccessError(CacheError):
    """Report an operating-system failure while accessing persistent cache state."""

    code = "cache_access"

    def __init__(self, path: str, operation: str) -> None:
        self.path = path
        self.operation = operation
        super().__init__(f"Could not {operation} cache path: {path}")
