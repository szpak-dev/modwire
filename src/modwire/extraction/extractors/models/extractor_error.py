from .extraction_error import ExtractionError


class ExtractorError(ExtractionError):
    """Base class for failures at a native extractor boundary."""

    code = "extractor_error"
