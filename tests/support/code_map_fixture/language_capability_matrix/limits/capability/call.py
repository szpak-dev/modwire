from pydantic import Field

from ....model import FixtureModel


class CallLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_resolutions: tuple[str, ...]
    absent_target_names: tuple[str, ...]
