from ....shared.failures.models.modwire_error import ModwireError


class ArchitectureConfigError(ModwireError):
    """Base class for architecture-configuration failures."""

    code = "architecture_config_error"
