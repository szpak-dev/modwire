from typing import Literal

from modwire.application import SourceSymbolKind

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class DeclarationObservation(FixtureModel):
    kind: Literal[ObservationKind.DECLARATION]
    qualified_name: QualifiedName
    declaration_kind: SourceSymbolKind
