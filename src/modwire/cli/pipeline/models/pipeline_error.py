from ....shared.failures.models.modwire_error import ModwireError
from ....shared.failures.models.modwire_error_code import ModwireErrorCode


class PipelineError(ModwireError):
    """Base class for CLI pipeline failures."""

    code = ModwireErrorCode.PIPELINE_ERROR
