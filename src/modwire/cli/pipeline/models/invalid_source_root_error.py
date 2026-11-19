from ....extraction.extractors.models.extraction_error import ExtractionError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class InvalidSourceRootError(ExtractionError):
    """Report a requested source root that is not a directory."""

    code = ModwireErrorCode.INVALID_SOURCE_ROOT

    def __init__(self, root: str) -> None:
        self.root = root
        super().__init__(f"Source root is not a directory: {root}")
