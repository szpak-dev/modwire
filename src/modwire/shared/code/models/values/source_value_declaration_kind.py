from enum import StrEnum


class SourceValueDeclarationKind(StrEnum):
    ASSIGNMENT = "assignment"
    CONSTANT = "constant"
    PROPERTY = "property"
    UNKNOWN = "unknown"
