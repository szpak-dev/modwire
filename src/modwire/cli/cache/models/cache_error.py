from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class CacheError(ModwireError):
    """Base class for persistent-cache ownership and access failures."""

    code = ModwireErrorCode.CACHE_ERROR
