from ....shared.failures.models.modwire_error import ModwireError


class ImplementationManifestError(ModwireError):
    """Base class for implementation-manifest contract failures."""

    code = "implementation_manifest_error"
