from ....fixture_model import FixtureModel
from ...values.enums.claim_state import ClaimState
from .observations.manifest import ManifestObservation


class ManifestClaim(FixtureModel):
    state: ClaimState
    observation: ManifestObservation
