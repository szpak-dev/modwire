from ....shared.failures.models.modwire_error import ModwireError


class ArchitectureError(ModwireError):
    """Base class for architecture configuration and analysis failures."""

    code = "architecture_error"
