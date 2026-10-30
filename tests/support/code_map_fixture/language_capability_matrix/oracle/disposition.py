from typing import Literal

from ...fixture_model import FixtureModel
from ..values.enums.claim_state import ClaimState
from ..values.enums.evidence_role import EvidenceRole
from ..values.names.scenario_id import ScenarioId


class ScenarioDisposition(FixtureModel):
    scenario: ScenarioId
    state: Literal[ClaimState.PRESENT]
    evidence: EvidenceRole
