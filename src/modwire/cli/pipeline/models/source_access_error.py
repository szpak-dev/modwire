from ....extraction.extractors.models.extraction_error import ExtractionError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class SourceAccessError(ExtractionError):
    """Report an operating-system failure while reading a source tree."""

    code = ModwireErrorCode.SOURCE_ACCESS

    def __init__(self, path: str, operation: str) -> None:
        self.path = path
        self.operation = operation
        super().__init__(f"Could not {operation} source path: {path}")
