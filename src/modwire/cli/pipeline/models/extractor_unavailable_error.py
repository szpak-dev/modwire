from ....extraction.extractors.models.extractor_error import ExtractorError


class ExtractorUnavailableError(ExtractorError):
    """Report a required extractor executable that is unavailable on PATH."""

    code = "extractor_unavailable"

    def __init__(self, language: str, executable: str) -> None:
        self.language = language
        self.executable = executable
        super().__init__(f"{language} extractor runtime is not available on PATH: {executable}")
