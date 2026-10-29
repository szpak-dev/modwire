from ...failures.models.modwire_error import ModwireError


class CodeError(ModwireError):
    """Base class for failures owned by the shared code contract."""

    code = "code_error"
