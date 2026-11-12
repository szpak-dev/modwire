from typing import Literal

from modwire.application import SourceDependencyResolution

from .....fixture_model import FixtureModel
from ....values.enums.observation_kind import ObservationKind
from ....values.names.identifier import Identifier
from ....values.paths.source_path import RepositorySourcePath


class ManifestDependencyObservation(FixtureModel):
    kind: Literal[ObservationKind.DEPENDENCY]
    source: RepositorySourcePath
    target: Identifier
    resolution: SourceDependencyResolution
