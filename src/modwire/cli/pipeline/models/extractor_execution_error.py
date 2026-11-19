from ....extraction.extractors.models.extractor_error import ExtractorError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class ExtractorExecutionError(ExtractorError):
    """Report a native extractor process that exited unsuccessfully."""

    code = ModwireErrorCode.EXTRACTOR_EXECUTION

    def __init__(self, language: str, exit_code: int, diagnostic: str) -> None:
        self.language = language
        self.exit_code = exit_code
        self.diagnostic = diagnostic
        super().__init__(f"{language} extractor failed with exit code {exit_code}: {diagnostic}")
