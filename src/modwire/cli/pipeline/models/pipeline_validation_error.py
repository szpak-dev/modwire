from .pipeline_error import PipelineError
from .pipeline_violation import PipelineViolation


class PipelineValidationError(PipelineError):
    code = "pipeline_validation"

    def __init__(self, violation: PipelineViolation, subject: str) -> None:
        self.violation = violation
        self.subject = subject
        super().__init__(f"Pipeline contract violates {violation}: {subject}.")
