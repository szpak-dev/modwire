from pydantic import Field

from ....model import FixtureModel


class NamespaceLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    absent_namespaces: tuple[str, ...]
