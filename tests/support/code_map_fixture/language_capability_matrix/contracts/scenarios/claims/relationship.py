from typing import Literal

from modwire.application import RelationshipFamily

from .....fixture_model import FixtureModel
from ....values.enums.claim_state import ClaimState
from ....values.enums.relationship_aspect import RelationshipAspect
from ..observations.relationship import RelationshipObservation


class RelationshipClaim(FixtureModel):
    kind: Literal["relationship"]
    relationship: RelationshipFamily
    aspect: RelationshipAspect
    state: ClaimState
    observation: RelationshipObservation
