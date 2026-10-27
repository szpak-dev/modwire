from pathlib import PurePosixPath

from pydantic import Field

from ...model import FixtureModel


class LanguageFixtureInventory(FixtureModel):
    reference_root: str = Field(min_length=1)
    capability_gap_root: str = Field(min_length=1)
    manifest_root: str = Field(min_length=1)
    manifest_sources: dict[str, str] = Field(min_length=1)

    def manifest_source(self, scenario: str) -> PurePosixPath:
        return PurePosixPath(self.manifest_sources[scenario])

    def manifest_scenario_root(self, scenario: str) -> PurePosixPath:
        return self.manifest_source(scenario).parents[1]
