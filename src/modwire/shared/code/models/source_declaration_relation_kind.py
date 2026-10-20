from enum import StrEnum


class SourceDeclarationRelationKind(StrEnum):
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    INCLUDES = "includes"
    PREPENDS = "prepends"
    EXTENDS_SINGLETON = "extends_singleton"
    USES_TRAIT = "uses_trait"
