from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .extraction_error import ExtractionError


class ExtractorError(ExtractionError):
    """Base class for failures at a native extractor boundary."""

    code = ModwireErrorCode.EXTRACTOR_ERROR
