from typing import Self

from pydantic import Field, model_validator

from modwire.application import CapabilityStatus

from ...model import FixtureModel
from .evidence import EvidenceExpectation


class CapabilityExpectation(FixtureModel):
    status: CapabilityStatus
    explanation: str = Field(min_length=1)
    limitation_scenarios: tuple[str, ...]
    evidence: EvidenceExpectation


class ParameterKindExpectation(FixtureModel):
    source: str = Field(min_length=1)
    present: tuple[str, ...]
    not_applicable: tuple[str, ...]

    @model_validator(mode="after")
    def validate_partition(self) -> Self:
        observed = (*self.present, *self.not_applicable)
        if len(observed) != len(set(observed)):
            raise ValueError("parameter kinds overlap")
        return self
