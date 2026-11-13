from enum import StrEnum


class SourceScopeKind(StrEnum):
    FILE = "file"
    DECLARATION = "declaration"
    BLOCK = "block"
