from typing import Literal

from modwire.application import SourceDependencyResolution

from .....fixture_model import FixtureModel
from ....values.names.identifier import Identifier
from ....values.paths.source_path import RepositorySourcePath


class ManifestDependencyObservation(FixtureModel):
    kind: Literal["dependency"]
    source: RepositorySourcePath
    target: Identifier
    resolution: SourceDependencyResolution
