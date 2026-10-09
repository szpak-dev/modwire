from enum import StrEnum


class ManifestDependencyTargetKind(StrEnum):
    SOURCE = "source"
    EXTERNAL = "external"
    UNRESOLVED = "unresolved"
