from .extraction_error import ExtractionError


class UnsupportedParserError(ExtractionError):
    """Report a language for which no in-process source parser is registered."""

    code = "unsupported_parser"

    def __init__(self, language: str, supported_languages: tuple[str, ...]) -> None:
        self.language = language
        self.supported_languages = supported_languages
        supported = ", ".join(supported_languages) or "none"
        super().__init__(f"In-process parsing is not supported for language: {language}. Supported: {supported}")
