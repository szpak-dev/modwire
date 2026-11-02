from typing import Self

from pydantic import model_validator

from ....fixture_model import FixtureModel
from ...values.paths.document_path import RepositoryDocumentPath
from ...values.paths.path import RepositoryPath


class FixtureCollection(FixtureModel):
    root: RepositoryPath
    resources: tuple[RepositoryDocumentPath, ...]

    @model_validator(mode="after")
    def validate_resources(self) -> Self:
        if len(set(self.resources)) != len(self.resources):
            raise ValueError("fixture collection resources contain duplicates")
        return self
