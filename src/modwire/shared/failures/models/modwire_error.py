from .modwire_error_code import ModwireErrorCode


class ModwireError(Exception):
    """Base class for every expected failure exposed by Modwire."""

    code: ModwireErrorCode = ModwireErrorCode.MODWIRE_ERROR
