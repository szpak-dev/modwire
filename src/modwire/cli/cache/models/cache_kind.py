from enum import StrEnum


class CacheKind(StrEnum):
    SOURCE = "source"
    SOURCE_SET = "source-set"
    CODE_MAP = "code-map"
    REPORTS = "reports"
