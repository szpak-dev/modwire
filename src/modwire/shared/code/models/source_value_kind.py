from enum import StrEnum


class SourceValueKind(StrEnum):
    CALLABLE = "callable"
    CLASS = "class"
    LITERAL = "literal"
    OBJECT = "object"
    UNKNOWN = "unknown"
