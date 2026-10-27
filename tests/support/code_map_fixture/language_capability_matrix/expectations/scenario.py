from pydantic import Field

from ...model import FixtureModel


class LimitationScenarioExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    source: str = Field(min_length=1)
    authored_syntax: tuple[str, ...] = Field(min_length=1)
