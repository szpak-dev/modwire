from .implementation_manifest_error import ImplementationManifestError
from .implementation_manifest_violation import ImplementationManifestViolation


class ImplementationManifestValidationError(ImplementationManifestError):
    """Report canonical implementation facts that violate the manifest contract."""

    code = "implementation_manifest_validation"

    def __init__(self, violation: ImplementationManifestViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Implementation manifest violates {violation}: {subject}.")
