from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .extraction_error import ExtractionError


class UnsupportedLanguageError(ExtractionError):
    """Report a language for which no source extractor is registered."""

    code = ModwireErrorCode.UNSUPPORTED_LANGUAGE

    def __init__(self, language: str, supported_languages: tuple[str, ...]) -> None:
        self.language = language
        self.supported_languages = supported_languages
        supported = ", ".join(supported_languages) or "none"
        super().__init__(f"Language is not supported: {language}. Supported languages: {supported}")
