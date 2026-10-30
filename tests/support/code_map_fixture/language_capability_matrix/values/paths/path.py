from pathlib import PurePosixPath
from typing import Self

from pydantic import model_validator

from ....fixture_root_model import FixtureRootModel


class RepositoryPath(FixtureRootModel[PurePosixPath]):
    @property
    def value(self) -> PurePosixPath:
        return self.root

    @model_validator(mode="after")
    def validate_relative(self) -> Self:
        if self.value.is_absolute() or ".." in self.value.parts:
            raise ValueError("repository paths must be normalized relative paths")
        return self
