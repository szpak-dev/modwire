from typing import Literal

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName
from ....values.numbers.position import SourcePosition


class ManifestParameterObservation(FixtureModel):
    kind: Literal[ObservationKind.PARAMETER]
    owner: QualifiedName
    position: SourcePosition
