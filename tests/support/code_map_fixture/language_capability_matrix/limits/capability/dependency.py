from pydantic import Field

from ....model import FixtureModel
from ...evidence.dependency import DependencyEvidence


class DependencyLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_dependencies: tuple[DependencyEvidence, ...]
    absent_dependencies: tuple[DependencyEvidence, ...]
