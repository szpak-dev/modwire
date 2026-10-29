from enum import StrEnum

from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation
from .fact_capability import FactCapability


class RelationshipFamily(StrEnum):
    """Language-neutral static relationship evidence families."""

    DECLARATION = "declaration"
    MEMBER = "member"
    DEPENDENCY = "dependency"

    @property
    def evidence_requirements(self) -> tuple[FactCapability, ...]:
        if self is RelationshipFamily.DECLARATION:
            return (
                FactCapability.SYMBOLS,
                FactCapability.INHERITANCE,
                FactCapability.DECLARATION_KINDS,
                FactCapability.COMPOSITION,
            )
        if self is RelationshipFamily.MEMBER:
            return (
                FactCapability.SYMBOLS,
                FactCapability.CALLABLES,
                FactCapability.CALLS,
                FactCapability.PARAMETERS,
                FactCapability.ANNOTATIONS,
                FactCapability.MODIFIERS,
                FactCapability.ATTRIBUTES,
                FactCapability.ASSIGNED_VALUES,
                FactCapability.DECLARATION_KINDS,
            )
        if self is RelationshipFamily.DEPENDENCY:
            return (FactCapability.SOURCES, FactCapability.DEPENDENCIES)
        raise CodeValidationError(CodeViolation.UNOWNED_RELATIONSHIP_FAMILY, self.value)
