from ....shared.failures.models.modwire_error import ModwireError


class ArchitectureShapeError(ModwireError):
    """Base class for architecture-shape failures."""

    code = "architecture_shape_error"
