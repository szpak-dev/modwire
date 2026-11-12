from typing import Literal

from modwire.application import SourceDeclarationRelationKind

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class ManifestDeclarationRelationObservation(FixtureModel):
    kind: Literal[ObservationKind.DECLARATION_RELATION]
    source: QualifiedName
    relation: SourceDeclarationRelationKind
    target: QualifiedName
