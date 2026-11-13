from enum import StrEnum


class SourceUnresolvedReason(StrEnum):
    EXTERNAL = "external"
    DYNAMIC = "dynamic"
    AMBIGUOUS = "ambiguous"
    UNOBSERVED = "unobserved"
