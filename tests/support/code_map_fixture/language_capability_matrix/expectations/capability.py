from pydantic import Field

from modwire.application import CapabilityStatus

from ...model import FixtureModel


class CapabilityExpectation(FixtureModel):
    status: CapabilityStatus
    explanation: str = Field(min_length=1)
    limitation_scenarios: tuple[str, ...]
