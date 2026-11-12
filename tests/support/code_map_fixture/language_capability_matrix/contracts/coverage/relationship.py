from modwire.application import CapabilityStatus

from ....fixture_model import FixtureModel


class RelationshipExpectation(FixtureModel):
    semantics: CapabilityStatus
    inventory: CapabilityStatus
