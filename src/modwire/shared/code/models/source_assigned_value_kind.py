from enum import StrEnum


class SourceAssignedValueKind(StrEnum):
    UNASSIGNED = "unassigned"
    CALL = "call"
    REFERENCE = "reference"
    LITERAL = "literal"
    UNRESOLVED = "unresolved"
    UNSUPPORTED = "unsupported"
