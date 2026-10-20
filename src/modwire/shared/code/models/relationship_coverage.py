from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .capability_status import CapabilityStatus
from .fact_capability import FactCapability
from .relationship_family import RelationshipFamily


class RelationshipCoverage(ValueModel):
    """An extractor's semantic and inventory support for one static relationship family."""

    family: RelationshipFamily
    evidence_requirements: tuple[FactCapability, ...]
    semantics: CapabilityStatus
    semantics_explanation: str = Field(min_length=1)
    inventory: CapabilityStatus
    inventory_explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_evidence_requirements(self) -> Self:
        if self.evidence_requirements != self.family.evidence_requirements:
            raise ValueError("Relationship coverage must declare the canonical evidence requirements.")
        return self
