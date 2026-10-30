from typing import Literal

from modwire.application import FactCapability

from .....fixture_model import FixtureModel
from ....values.enums.claim_state import ClaimState
from ..observations.capability import CapabilityObservation


class CapabilityClaim(FixtureModel):
    kind: Literal["capability"]
    capability: FactCapability
    state: ClaimState
    observation: CapabilityObservation
