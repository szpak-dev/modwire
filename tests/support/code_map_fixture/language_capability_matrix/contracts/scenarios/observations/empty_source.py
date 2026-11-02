from typing import Literal

from .....fixture_model import FixtureModel
from ....values.paths.source_path import RepositorySourcePath


class EmptySourceObservation(FixtureModel):
    kind: Literal["empty_source"]
    relative_path: RepositorySourcePath
