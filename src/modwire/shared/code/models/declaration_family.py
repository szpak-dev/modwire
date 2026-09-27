from enum import StrEnum


class DeclarationFamily(StrEnum):
    CLASS = "class"
    ABSTRACT_CLASS = "abstract_class"
    INTERFACE = "interface"
    TYPE = "type"
    FUNCTION = "function"
    METHOD = "method"
    VALUE = "value"
    CALLABLE = "callable"
