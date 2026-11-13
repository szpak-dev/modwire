from enum import StrEnum


class InventoryLimitationKind(StrEnum):
    UNSUPPORTED_SYNTAX = "unsupported_syntax"
    UNVISITED_SCOPE = "unvisited_scope"
    UNRESOLVED_OWNERSHIP = "unresolved_ownership"
    DYNAMIC_STRUCTURE = "dynamic_structure"
