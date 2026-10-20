from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .capability_coverage import CapabilityCoverage
from .extractor_descriptor import ExtractorDescriptor
from .fact_capability import FactCapability
from .relationship_coverage import RelationshipCoverage
from .relationship_family import RelationshipFamily


class CodeMapProducer(ValueModel):
    modwire_version: str = Field(min_length=1)
    extractor: ExtractorDescriptor
    capabilities: tuple[CapabilityCoverage, ...]
    relationship_capabilities: tuple[RelationshipCoverage, ...]

    @model_validator(mode="after")
    def validate_coverage(self) -> Self:
        declared = tuple(item.capability for item in self.capabilities)
        if len(declared) != len(set(declared)):
            raise ValueError("Producer capability coverage contains duplicate fact families.")
        if set(declared) != set(FactCapability):
            raise ValueError("Producer capability coverage must classify every fact family.")
        order = {capability: position for position, capability in enumerate(FactCapability)}
        if self.capabilities != tuple(sorted(self.capabilities, key=lambda item: order[item.capability])):
            raise ValueError("Producer capability coverage must be canonically ordered.")
        relationship_declared = tuple(item.family for item in self.relationship_capabilities)
        if len(relationship_declared) != len(set(relationship_declared)):
            raise ValueError("Producer relationship coverage contains duplicate families.")
        if set(relationship_declared) != set(RelationshipFamily):
            raise ValueError("Producer relationship coverage must classify every relationship family.")
        relationship_order = {family: position for position, family in enumerate(RelationshipFamily)}
        if self.relationship_capabilities != tuple(
            sorted(self.relationship_capabilities, key=lambda item: relationship_order[item.family])
        ):
            raise ValueError("Producer relationship coverage must be canonically ordered.")
        return self
