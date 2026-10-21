from enum import StrEnum


class PipelineViolation(StrEnum):
    INVALID_PARALLEL_SIZE = "invalid_parallel_size"
    MISSING_REPORT = "missing_report"
    CONFIGURATION_ACCESS_FAILED = "configuration_access_failed"
    CONFIGURATION_PARSE_FAILED = "configuration_parse_failed"
