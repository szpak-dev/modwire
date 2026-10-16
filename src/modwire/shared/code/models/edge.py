from typing import Self

from pydantic import ConfigDict, model_validator

from ...values.models.value_model import ValueModel
from .identity import FileId, ImportSpecifier
from .source_dependency_kind import SourceDependencyKind
from .source_dependency_resolution import SourceDependencyResolution


class Edge(ValueModel):
    model_config = ConfigDict(frozen=True)
    from_id: FileId
    to_id: FileId | None
    specifier: ImportSpecifier
    resolution: SourceDependencyResolution
    kind: SourceDependencyKind = SourceDependencyKind.IMPORTS

    @model_validator(mode="after")
    def validate_relation_kind(self) -> Self:
        if self.kind is not SourceDependencyKind.IMPORTS:
            raise ValueError("Dependency edges must use imports.")
        return self
