from enum import StrEnum


class SourceValueScope(StrEnum):
    MODULE = "module"
    LOCAL = "local"
    MEMBER = "member"
