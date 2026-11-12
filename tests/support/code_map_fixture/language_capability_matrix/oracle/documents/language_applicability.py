from typing import Self

from pydantic import Field, model_validator

from ....fixture_model import FixtureModel
from ....scenario_contract_error import ScenarioContractError
from ....scenario_violation import ScenarioViolation
from ...values.names.scenario_id import ScenarioId


class LanguageApplicability(FixtureModel):
    applicable: bool
    reason: str = Field(min_length=1)
    evidence: tuple[ScenarioId, ...]

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        if len(set(self.evidence)) != len(self.evidence) or (not self.applicable and self.evidence):
            raise ScenarioContractError(ScenarioViolation.OBLIGATION_COVERAGE, "inconsistent scenario evidence")
        return self
