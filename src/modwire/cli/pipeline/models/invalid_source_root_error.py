from ....extraction.extractors.models.extraction_error import ExtractionError


class InvalidSourceRootError(ExtractionError):
    """Report a requested source root that is not a directory."""

    code = "invalid_source_root"

    def __init__(self, root: str) -> None:
        self.root = root
        super().__init__(f"Source root is not a directory: {root}")
