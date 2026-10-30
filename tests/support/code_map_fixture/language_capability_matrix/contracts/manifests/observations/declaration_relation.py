from typing import Literal

from modwire.application import SourceDeclarationRelationKind

from .....fixture_model import FixtureModel
from ....values.names.qualified_name import QualifiedName


class ManifestDeclarationRelationObservation(FixtureModel):
    kind: Literal["declaration_relation"]
    source: QualifiedName
    relation: SourceDeclarationRelationKind
    target: QualifiedName
