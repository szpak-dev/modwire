from enum import StrEnum


class SourceRelationKind(StrEnum):
    """Canonical relation kinds published by code maps and implementation manifests."""

    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    IMPORTS = "imports"
