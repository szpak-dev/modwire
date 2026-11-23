from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class InitializationError(ModwireError):
    """Base class for project initialization failures."""

    code = ModwireErrorCode.INITIALIZATION_ERROR
