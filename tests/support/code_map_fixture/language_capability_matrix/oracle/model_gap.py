from typing import Literal, Self

from pydantic import Field, model_validator

from ...conclusion import Conclusion
from ...discrepancy import Discrepancy
from ...fixture_model import FixtureModel
from ...scenario_contract_error import ScenarioContractError
from ...scenario_violation import ScenarioViolation


class ModelGapExpectation(FixtureModel):
    conclusion: Conclusion
    state: Literal[Discrepancy.MODEL_GAP, Discrepancy.UNASSESSED]
    missing_representation: str = Field(min_length=1)
    owner_issue: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_conclusion(self) -> Self:
        if self.conclusion is Conclusion.CONTRACT:
            raise ScenarioContractError(ScenarioViolation.OBLIGATION_COVERAGE, "model gap outside source obligations")
        return self
