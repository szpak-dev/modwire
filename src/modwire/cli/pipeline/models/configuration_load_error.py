from .pipeline_error import PipelineError
from .pipeline_violation import PipelineViolation


class ConfigurationLoadError(PipelineError):
    """Report an architecture-configuration resource that cannot be loaded."""

    code = "configuration_load"

    def __init__(self, violation: PipelineViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Configuration load violates {violation}: {subject}.")
