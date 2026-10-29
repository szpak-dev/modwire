from pathlib import PurePosixPath

from pydantic import Field

from ...model import FixtureModel


class LanguageFixtureInventory(FixtureModel):
    reference_root: str = Field(min_length=1)
    capability_gap_root: str = Field(min_length=1)
    type_reference_cases: str = Field(min_length=1)
    type_reference_empty: str = Field(min_length=1)
    manifest_root: str = Field(min_length=1)
    manifest_sources: dict[str, str] = Field(min_length=1)

    def type_reference_sources(self) -> tuple[PurePosixPath, PurePosixPath]:
        return (PurePosixPath(self.type_reference_cases), PurePosixPath(self.type_reference_empty))

    def type_reference_root(self) -> PurePosixPath:
        return PurePosixPath(self.type_reference_cases).parents[1]

    def manifest_source(self, scenario: str) -> PurePosixPath:
        return PurePosixPath(self.manifest_sources[scenario])

    def manifest_scenario_root(self, scenario: str) -> PurePosixPath:
        return self.manifest_source(scenario).parents[1]
