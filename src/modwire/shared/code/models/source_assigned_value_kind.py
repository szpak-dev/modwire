from enum import StrEnum


class SourceAssignedValueKind(StrEnum):
    """Kinds of class-property assignment evidence published by extractors."""

    UNASSIGNED = "unassigned"
    CALL = "call"
    REFERENCE = "reference"
    LITERAL = "literal"
    UNRESOLVED = "unresolved"
    UNSUPPORTED = "unsupported"
