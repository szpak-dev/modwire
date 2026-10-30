from ...fixture_model import FixtureModel
from ..values.enums.claim_state import ClaimState
from ..values.enums.evidence_role import EvidenceRole
from .reference import FixtureFactReference


class ScenarioFactExpectation(FixtureModel):
    fact: FixtureFactReference
    state: ClaimState
    evidence: EvidenceRole
