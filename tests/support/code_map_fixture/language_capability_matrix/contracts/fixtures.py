from pydantic import Field

from ...model import FixtureModel
from ..values import RepositoryPath, RepositorySourcePath, SourceSuffix


class FixtureSourceSet(FixtureModel):
    root: RepositoryPath
    sources: tuple[RepositorySourcePath, ...] = Field(min_length=1)


class LanguageFixtureInventory(FixtureModel):
    source_suffixes: tuple[SourceSuffix, ...] = Field(min_length=1)
    extensions: FixtureSourceSet
    gaps: FixtureSourceSet
    types: FixtureSourceSet
    parameters: FixtureSourceSet
