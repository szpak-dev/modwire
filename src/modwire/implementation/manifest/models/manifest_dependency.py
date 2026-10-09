from typing import Self

from pydantic import model_validator

from ....shared.code.models.source_dependency_resolution import SourceDependencyResolution
from ....shared.code.models.source_relation_kind import SourceRelationKind
from ....shared.values.models.value_model import ValueModel
from .manifest_dependency_target_kind import ManifestDependencyTargetKind


class ManifestDependency(ValueModel):
    source_id: str
    target_kind: ManifestDependencyTargetKind
    target: str
    specifier: str
    resolution: SourceDependencyResolution
    kind: SourceRelationKind

    @model_validator(mode="after")
    def validate_relation_kind(self) -> Self:
        if self.kind is not SourceRelationKind.IMPORTS:
            raise ValueError("Manifest dependencies must use imports.")
        return self
