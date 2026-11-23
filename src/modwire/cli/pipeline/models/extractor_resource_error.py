from ....extraction.extractors.models.extractor_error import ExtractorError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class ExtractorResourceError(ExtractorError):
    """Report a missing or unreadable packaged extractor resource."""

    code = ModwireErrorCode.EXTRACTOR_RESOURCE

    def __init__(self, language: str, resource: str) -> None:
        self.language = language
        self.resource = resource
        super().__init__(f"{language} extractor resource is unavailable: {resource}")
