from typing import Literal

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.paths.source_path import RepositorySourcePath


class EmptySourceObservation(FixtureModel):
    kind: Literal[ObservationKind.EMPTY_SOURCE]
    relative_path: RepositorySourcePath
