from ....shared.failures.models.modwire_error_code import ModwireErrorCode
from .initialization_error import InitializationError


class InvalidInitializationTargetError(InitializationError):
    """Report an initialization target outside the accepted project boundary."""

    code = ModwireErrorCode.INVALID_INITIALIZATION_TARGET

    def __init__(self, target: str, reason: str) -> None:
        self.target = target
        self.reason = reason
        super().__init__(f"Invalid initialization target {target}: {reason}")
