from enum import StrEnum


class SourceDependencyResolution(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    EXTERNAL = "external"
