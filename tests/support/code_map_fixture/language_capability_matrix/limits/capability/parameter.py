from pydantic import Field

from ....model import FixtureModel


class ParameterLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_parameter_kinds: tuple[str, ...]
    unrepresented_authored_parameters: tuple[str, ...]
