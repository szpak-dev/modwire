from ....shared.failures.models.modwire_error import ModwireError


class InitializationError(ModwireError):
    """Base class for project initialization failures."""

    code = "initialization_error"
