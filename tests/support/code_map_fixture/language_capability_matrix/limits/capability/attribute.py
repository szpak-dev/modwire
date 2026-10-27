from pydantic import Field

from ....model import FixtureModel


class AttributeLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_attribute_names: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]
