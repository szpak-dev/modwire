from typing import Literal

from modwire.application import SourceNamespaceKind

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class NamespaceObservation(FixtureModel):
    kind: Literal[ObservationKind.NAMESPACE]
    qualified_name: QualifiedName
    namespace_kind: SourceNamespaceKind
