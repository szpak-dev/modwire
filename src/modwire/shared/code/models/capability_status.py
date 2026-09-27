from enum import StrEnum


class CapabilityStatus(StrEnum):
    """Declared completeness of an extractor's support for a fact family."""

    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
