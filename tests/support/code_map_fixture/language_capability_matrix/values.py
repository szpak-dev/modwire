from pathlib import PurePosixPath

from pydantic import Field, model_validator

from ..model import FixtureRootModel


class RepositoryPath(FixtureRootModel[PurePosixPath]):
    @property
    def value(self) -> PurePosixPath:
        return self.root

    @model_validator(mode="after")
    def validate_relative(self) -> "RepositoryPath":
        if self.value.is_absolute() or ".." in self.value.parts:
            raise ValueError("repository paths must be normalized relative paths")
        return self


class RepositorySourcePath(RepositoryPath):
    pass


class RepositoryDocumentPath(RepositoryPath):
    pass


class Identifier(FixtureRootModel[str]):
    root: str = Field(min_length=1)

    @property
    def value(self) -> str:
        return self.root


class SourceSuffix(FixtureRootModel[str]):
    root: str = Field(pattern=r"^\.[a-z0-9]+$")

    @property
    def value(self) -> str:
        return self.root


class AuthoredSyntax(Identifier):
    pass


class LanguageId(Identifier):
    pass


class ScenarioId(Identifier):
    pass


class ManifestScenarioId(ScenarioId):
    pass
