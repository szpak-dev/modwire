from pydantic import Field

from ...model import FixtureModel
from ..values import RepositoryPath, RepositorySourcePath, SourceSuffix


class FixtureSourceSet(FixtureModel):
    root: RepositoryPath
    sources: tuple[RepositorySourcePath, ...] = Field(min_length=1)


class TypeReferenceFixtures(FixtureModel):
    root: RepositoryPath
    cases: RepositorySourcePath
    empty: RepositorySourcePath


class ManifestFixtureInventory(FixtureModel):
    root: RepositoryPath
    sources: dict[str, RepositorySourcePath] = Field(min_length=1)


class LanguageFixtureInventory(FixtureModel):
    source_suffixes: tuple[SourceSuffix, ...] = Field(min_length=1)
    reference: FixtureSourceSet
    language_extensions: FixtureSourceSet
    capability_gaps: FixtureSourceSet
    type_references: TypeReferenceFixtures
    parameter_kinds: FixtureSourceSet
    manifests: ManifestFixtureInventory
