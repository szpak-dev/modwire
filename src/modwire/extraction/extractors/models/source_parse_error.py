from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .extractor_error import ExtractorError


class SourceParseError(ExtractorError):
    """Report source text rejected by an extractor's parser."""

    code = ModwireErrorCode.SOURCE_PARSE

    def __init__(
        self,
        language: str,
        path: str,
        line: int,
        column: int,
        diagnostic: str,
    ) -> None:
        self.language = language
        self.path = path
        self.line = line
        self.column = column
        self.diagnostic = diagnostic
        super().__init__(f"Could not parse {language} source {path}:{line}:{column}: {diagnostic}")
