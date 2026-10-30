from modwire.application import CapabilityStatus

from ....fixture_model import FixtureModel
from ...values.names.capability_explanation import CapabilityExplanation


class RelationshipExpectation(FixtureModel):
    semantics: CapabilityStatus
    semantics_explanation: CapabilityExplanation
    inventory: CapabilityStatus
    inventory_explanation: CapabilityExplanation
