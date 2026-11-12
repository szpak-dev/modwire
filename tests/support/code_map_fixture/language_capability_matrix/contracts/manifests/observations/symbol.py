from typing import Literal

from modwire.application import SourceSymbolKind

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class ManifestSymbolObservation(FixtureModel):
    kind: Literal[ObservationKind.SYMBOL]
    qualified_name: QualifiedName
    symbol_kind: SourceSymbolKind
