from typing import Literal, Self

from pydantic import model_validator

from ....shared.code.models.source_relation_kind import SourceRelationKind
from ....shared.values.models.value_model import ValueModel


class ManifestDependency(ValueModel):
    source_id: str
    target_kind: Literal["source", "external", "unresolved"]
    target: str
    specifier: str
    resolution: Literal["resolved", "external", "unresolved"]
    kind: SourceRelationKind

    @model_validator(mode="after")
    def validate_relation_kind(self) -> Self:
        if self.kind is not SourceRelationKind.IMPORTS:
            raise ValueError("Manifest dependencies must use imports.")
        return self
