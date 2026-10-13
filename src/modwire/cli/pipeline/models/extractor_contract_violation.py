from enum import StrEnum


class ExtractorContractViolation(StrEnum):
    """Identify the extractor contract clause violated by runtime output."""

    EMPTY_RUNTIME_VERSION = "empty_runtime_version"
    INVALID_OUTPUT = "invalid_output"
    SOURCE_SET_MISMATCH = "source_set_mismatch"
