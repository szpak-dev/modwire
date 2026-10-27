from pydantic import Field

from ....model import FixtureModel


class CallableLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_callable_names: tuple[str, ...]
    absent_callable_names: tuple[str, ...]
