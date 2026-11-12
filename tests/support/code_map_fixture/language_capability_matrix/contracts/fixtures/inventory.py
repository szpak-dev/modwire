from typing import Self

from pydantic import Field, model_validator

from ....fixture_model import FixtureModel
from ...values.enums.fixture_role import FixtureRole
from ...values.names.source_suffix import SourceSuffix
from .source_set import FixtureSourceSet


class LanguageFixtureInventory(FixtureModel):
    source_suffixes: tuple[SourceSuffix, ...] = Field(min_length=1)
    extensions: FixtureSourceSet
    gaps: FixtureSourceSet
    types: FixtureSourceSet
    parameters: FixtureSourceSet
    structural: FixtureSourceSet

    @model_validator(mode="after")
    def validate_suffixes(self) -> Self:
        if len(set(self.source_suffixes)) != len(self.source_suffixes):
            raise ValueError("source suffix inventory contains duplicates")
        return self

    def source_sets(self) -> dict[FixtureRole, FixtureSourceSet]:
        return {
            FixtureRole.EXTENSIONS: self.extensions,
            FixtureRole.GAPS: self.gaps,
            FixtureRole.TYPES: self.types,
            FixtureRole.PARAMETERS: self.parameters,
            FixtureRole.STRUCTURAL: self.structural,
        }
