from pydantic import Field

from ....model import FixtureModel


class SymbolLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_declaration_names: tuple[str, ...]
    absent_declaration_names: tuple[str, ...]
