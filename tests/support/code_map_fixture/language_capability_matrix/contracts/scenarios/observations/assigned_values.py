from typing import Literal

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class AssignedValuesObservation(FixtureModel):
    kind: Literal[ObservationKind.ASSIGNED_VALUES]
    owner: QualifiedName
