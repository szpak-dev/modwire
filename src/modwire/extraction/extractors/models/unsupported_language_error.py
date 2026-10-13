from .extraction_error import ExtractionError


class UnsupportedLanguageError(ExtractionError):
    """Report a language for which no source extractor is registered."""

    code = "unsupported_language"

    def __init__(self, language: str, supported_languages: tuple[str, ...]) -> None:
        self.language = language
        self.supported_languages = supported_languages
        supported = ", ".join(supported_languages) or "none"
        super().__init__(f"Language is not supported: {language}. Supported languages: {supported}")
