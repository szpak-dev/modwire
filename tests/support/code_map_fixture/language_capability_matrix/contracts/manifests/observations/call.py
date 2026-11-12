from typing import Literal

from modwire.application import SourceCallResolution

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.qualified_name import QualifiedName


class ManifestCallObservation(FixtureModel):
    kind: Literal[ObservationKind.CALL]
    owner: QualifiedName
    target: QualifiedName
    resolution: SourceCallResolution
