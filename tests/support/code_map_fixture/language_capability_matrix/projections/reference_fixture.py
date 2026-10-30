from pydantic import Field

from ...fixture_model import FixtureModel
from ..values.paths.path import RepositoryPath
from ..values.paths.source_path import RepositorySourcePath


class ReferenceFixtureInventory(FixtureModel):
    root: RepositoryPath
    sources: tuple[RepositorySourcePath, ...] = Field(min_length=1)
