from pydantic import Field

from ...values.models.value_model import ValueModel
from .capability_status import CapabilityStatus
from .fact_capability import FactCapability


class CapabilityCoverage(ValueModel):
    """An extractor's explicit support status for one implementation fact family."""

    capability: FactCapability
    status: CapabilityStatus
    explanation: str = Field(min_length=1)
