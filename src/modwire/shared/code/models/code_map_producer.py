from typing import Self

from pydantic import Field, model_validator

from ...values.models.value_model import ValueModel
from .capability_coverage import CapabilityCoverage
from .extractor_descriptor import ExtractorDescriptor
from .fact_capability import FactCapability


class CodeMapProducer(ValueModel):
    modwire_version: str = Field(min_length=1)
    extractor: ExtractorDescriptor
    capabilities: tuple[CapabilityCoverage, ...]

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
        return self
