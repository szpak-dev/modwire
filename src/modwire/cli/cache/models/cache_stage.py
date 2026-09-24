from enum import StrEnum


class CacheStage(StrEnum):
    """Public stages reported by cached Modwire operations."""

    EXTRACTION = "extraction"
    CODE_MAP = "code-map"
    REPORTS = "reports"
