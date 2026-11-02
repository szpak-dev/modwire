from typing import Literal

from ....fixture_model import FixtureModel
from ...values.enums.claim_state import ClaimState
from .observations.manifest import ManifestObservation


class ManifestClaim(FixtureModel):
    state: Literal[ClaimState.PRESENT, ClaimState.ABSENT]
    observation: ManifestObservation
