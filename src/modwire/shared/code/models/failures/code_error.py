from ....failures.models.modwire_error import ModwireError
from ....failures.models.modwire_error_code import ModwireErrorCode


class CodeError(ModwireError):
    """Base class for failures owned by the shared code contract."""

    code = ModwireErrorCode.CODE_ERROR
