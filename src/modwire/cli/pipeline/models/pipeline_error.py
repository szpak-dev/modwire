from ....shared.failures.models.modwire_error import ModwireError


class PipelineError(ModwireError):
    """Base class for CLI pipeline failures."""

    code = "pipeline_error"
