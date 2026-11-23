from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class ArchitectureShapeError(ModwireError):
    """Base class for architecture-shape failures."""

    code = ModwireErrorCode.ARCHITECTURE_SHAPE_ERROR
