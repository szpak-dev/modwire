from pydantic import Field

from modwire.application import CapabilityStatus

from ...model import FixtureModel
from .evidence import EvidenceExpectation


class RelationshipExpectation(FixtureModel):
    semantics: CapabilityStatus
    semantics_explanation: str = Field(min_length=1)
    semantics_limitation_scenarios: tuple[str, ...]
    inventory: CapabilityStatus
    inventory_explanation: str = Field(min_length=1)
    inventory_limitation_scenarios: tuple[str, ...]
    evidence: EvidenceExpectation
