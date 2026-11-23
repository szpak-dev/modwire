from enum import StrEnum

from ..declarations.declaration_family import DeclarationFamily


class SourceCallableKind(StrEnum):
    FUNCTION = "function"
    INSTANCE_METHOD = "instance_method"
    TYPE_METHOD = "type_method"
    STATIC_METHOD = "static_method"
    CONSTRUCTOR = "constructor"
    CALLABLE_VALUE = "callable_value"
    ANONYMOUS = "anonymous"

    @property
    def declaration_family(self) -> DeclarationFamily:
        if self is SourceCallableKind.FUNCTION:
            return DeclarationFamily.FUNCTION
        if self is SourceCallableKind.CALLABLE_VALUE:
            return DeclarationFamily.VALUE
        if self is SourceCallableKind.ANONYMOUS:
            return DeclarationFamily.CALLABLE
        return DeclarationFamily.METHOD
