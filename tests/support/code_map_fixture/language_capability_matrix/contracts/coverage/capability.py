from modwire.application import CapabilityStatus

from ....fixture_model import FixtureModel


class CapabilityExpectation(FixtureModel):
    status: CapabilityStatus
