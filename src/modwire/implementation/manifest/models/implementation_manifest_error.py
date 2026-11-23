from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class ImplementationManifestError(ModwireError):
    """Base class for implementation-manifest contract failures."""

    code = ModwireErrorCode.IMPLEMENTATION_MANIFEST_ERROR
