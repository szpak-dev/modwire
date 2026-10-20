from pathlib import PurePosixPath
from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation


class SourceArtifact(ValueModel):
    source_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    content_digest: str = Field(pattern="^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_relative_path(self) -> Self:
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise CodeValidationError(CodeViolation.NON_NORMALIZED_SOURCE_ARTIFACT_PATH, self.relative_path)
        return self
