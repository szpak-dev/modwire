from ....extraction.extractors.models.extractor_error import ExtractorError


class ExtractorResourceError(ExtractorError):
    """Report a missing or unreadable packaged extractor resource."""

    code = "extractor_resource"

    def __init__(self, language: str, resource: str) -> None:
        self.language = language
        self.resource = resource
        super().__init__(f"{language} extractor resource is unavailable: {resource}")
