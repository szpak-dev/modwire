from typing import Literal

from modwire.application import SourceCallableKind

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class CallableObservation(FixtureModel):
    kind: Literal[ObservationKind.CALLABLE]
    qualified_name: QualifiedName
    callable_kind: SourceCallableKind
