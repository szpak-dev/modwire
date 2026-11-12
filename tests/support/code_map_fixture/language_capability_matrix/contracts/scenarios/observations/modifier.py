from typing import Literal

from modwire.application import SourceVisibility

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class ModifierObservation(FixtureModel):
    kind: Literal[ObservationKind.MODIFIER]
    owner: QualifiedName
    visibility: SourceVisibility
