from ....shared.failures.models.modwire_error import ModwireError


class CacheError(ModwireError):
    """Base class for persistent-cache ownership and access failures."""

    code = "cache_error"
