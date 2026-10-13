from .implementation_manifest_error import ImplementationManifestError
from .manifest_format import ManifestFormat


class UnsupportedManifestFormatError(ImplementationManifestError):
    """Report an implementation-manifest format with no matching serializer."""

    code = "unsupported_manifest_format"

    def __init__(self, format: ManifestFormat, supported_formats: tuple[ManifestFormat, ...]) -> None:
        self.format = format
        self.supported_formats = supported_formats
        supported = ", ".join(item.id for item in supported_formats) or "none"
        super().__init__(f"Implementation manifest format is not supported: {format.id}. Supported: {supported}")
