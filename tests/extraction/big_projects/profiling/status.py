from enum import StrEnum


class ProfileStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
