from typing import Self

from pydantic import model_validator

from ....values.models.value_model import ValueModel
from ..failures.code_validation_error import CodeValidationError
from ..failures.code_violation import CodeViolation
from ..sources.identity import FileId, ImportSpecifier
from .source_dependency_kind import SourceDependencyKind
from .source_dependency_resolution import SourceDependencyResolution


class Edge(ValueModel):
    from_id: FileId
    to_id: FileId | None
    specifier: ImportSpecifier
    resolution: SourceDependencyResolution
    kind: SourceDependencyKind = SourceDependencyKind.IMPORTS

    @model_validator(mode="after")
    def validate_relation_kind(self) -> Self:
        if self.kind is not SourceDependencyKind.IMPORTS:
            raise CodeValidationError(CodeViolation.NON_IMPORT_DEPENDENCY_EDGE, self.kind)
        return self
