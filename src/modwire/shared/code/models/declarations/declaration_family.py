from enum import StrEnum


class DeclarationFamily(StrEnum):
    CLASS = "class"
    ABSTRACT_CLASS = "abstract_class"
    INTERFACE = "interface"
    TYPE = "type"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    VALUE = "value"
    CALLABLE = "callable"
