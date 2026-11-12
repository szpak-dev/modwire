from typing import Literal

from modwire.application import RelationshipFamily

from .....fixture_model import FixtureModel
from ....values.enums.claim_kind import ClaimKind
from ....values.enums.claim_state import ClaimState
from ....values.enums.evidence_role import EvidenceRole
from ....values.enums.relationship_aspect import RelationshipAspect
from ..observations.relationship import RelationshipObservation


class RelationshipClaim(FixtureModel):
    kind: Literal[ClaimKind.RELATIONSHIP]
    relationship: RelationshipFamily
    aspect: RelationshipAspect
    evidence: EvidenceRole
    state: ClaimState
    observation: RelationshipObservation
