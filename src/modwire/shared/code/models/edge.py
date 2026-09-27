from typing import Self

from pydantic import ConfigDict, model_validator

from ...values.models.value_model import ValueModel
from .edge_resolution import EdgeResolution
from .identity import FileId, ImportSpecifier
from .source_relation_kind import SourceRelationKind


class Edge(ValueModel):
    model_config = ConfigDict(frozen=True)
    from_id: FileId
    to_id: FileId | None
    specifier: ImportSpecifier
    resolution: EdgeResolution
    kind: SourceRelationKind = SourceRelationKind.IMPORTS

    @model_validator(mode="after")
    def validate_relation_kind(self) -> Self:
        if self.kind is not SourceRelationKind.IMPORTS:
            raise ValueError("Dependency edges must use imports.")
        return self
