from pydantic import Field

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

    def source_sets(self) -> dict[FixtureRole, FixtureSourceSet]:
        return {
            FixtureRole.EXTENSIONS: self.extensions,
            FixtureRole.GAPS: self.gaps,
            FixtureRole.TYPES: self.types,
            FixtureRole.PARAMETERS: self.parameters,
        }
