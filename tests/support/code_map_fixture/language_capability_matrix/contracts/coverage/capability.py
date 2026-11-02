from modwire.application import CapabilityStatus

from ....fixture_model import FixtureModel
from ...values.names.capability_explanation import CapabilityExplanation


class CapabilityExpectation(FixtureModel):
    status: CapabilityStatus
    explanation: CapabilityExplanation
