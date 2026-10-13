from .implementation_manifest_error import ImplementationManifestError


class InvalidImplementationManifestError(ImplementationManifestError):
    """Report a manifest document or serializer that violates its declared format contract."""

    code = "invalid_implementation_manifest"

    def __init__(self, format_id: str, reason: str) -> None:
        self.format_id = format_id
        self.reason = reason
        super().__init__(f"Invalid implementation manifest for format {format_id!r}: {reason}")
