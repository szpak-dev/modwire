from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .implementation_manifest_error import ImplementationManifestError


class InvalidImplementationManifestError(ImplementationManifestError):
    """Report a manifest document or serializer that violates its declared format contract."""

    code = ModwireErrorCode.INVALID_IMPLEMENTATION_MANIFEST

    def __init__(self, format_id: str, reason: str) -> None:
        self.format_id = format_id
        self.reason = reason
        super().__init__(f"Invalid implementation manifest for format {format_id!r}: {reason}")
