from enum import StrEnum


class ProfileResourceReason(StrEnum):
    WITHIN_LIMITS = "within_limits"
    RSS_LIMIT = "rss_limit"
    PROCESS_LIMIT = "process_limit"
    MONITOR_FAILED = "monitor_failed"
