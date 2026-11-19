from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class ExtractionError(ModwireError):
    """Base class for failures while discovering, extracting, or parsing source code."""

    code = ModwireErrorCode.EXTRACTION_ERROR
