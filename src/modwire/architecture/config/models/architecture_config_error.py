from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class ArchitectureConfigError(ModwireError):
    """Base class for architecture-configuration failures."""

    code = ModwireErrorCode.ARCHITECTURE_CONFIG_ERROR
