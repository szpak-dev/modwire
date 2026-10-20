from enum import StrEnum


class PipelineViolation(StrEnum):
    INVALID_PARALLEL_SIZE = "invalid_parallel_size"
    MISSING_REPORT = "missing_report"
