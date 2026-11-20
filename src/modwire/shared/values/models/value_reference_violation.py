from enum import StrEnum


class ValueReferenceViolation(StrEnum):
    MISSING_CONTEXT = "missing_context"
    INVALID_INDEX = "invalid_index"
