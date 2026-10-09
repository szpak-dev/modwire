from enum import StrEnum


class SourceCallResolution(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    EXTERNAL = "external"
    DYNAMIC = "dynamic"
