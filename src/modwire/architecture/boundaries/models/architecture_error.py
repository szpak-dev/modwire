from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class ArchitectureError(ModwireError):
    """Base class for architecture configuration and analysis failures."""

    code = ModwireErrorCode.ARCHITECTURE_ERROR
