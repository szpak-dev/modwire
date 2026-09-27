from enum import StrEnum


class SourceMemberKind(StrEnum):
    """Ownership kind for a declared class or type member."""

    INSTANCE = "instance"
    STATIC = "static"
