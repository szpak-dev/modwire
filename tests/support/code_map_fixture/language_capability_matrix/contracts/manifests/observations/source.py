from typing import Literal

from .....fixture_model import FixtureModel
from ....values.paths.source_path import RepositorySourcePath


class ManifestSourceObservation(FixtureModel):
    kind: Literal["source"]
    relative_path: RepositorySourcePath
