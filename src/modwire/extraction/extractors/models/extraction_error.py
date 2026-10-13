from ....shared.failures.models.modwire_error import ModwireError


class ExtractionError(ModwireError):
    """Base class for failures while discovering, extracting, or parsing source code."""

    code = "extraction_error"
