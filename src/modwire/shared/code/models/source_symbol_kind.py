from enum import StrEnum


class SourceSymbolKind(StrEnum):
    CLASS = "class"
    ABSTRACT_CLASS = "abstract_class"
    INTERFACE = "interface"
    RECORD = "record"
    ENUM = "enum"
    ANNOTATION = "annotation"
    TRAIT = "trait"
    MODULE = "module"
    TYPE_ALIAS = "type_alias"
    FUNCTION = "function"
    CALLABLE = "callable"
    VALUE_CALLABLE = "value_callable"
    VALUE_CLASS = "value_class"
    VALUE_LITERAL = "value_literal"
    VALUE_OBJECT = "value_object"
    VALUE_UNKNOWN = "value_unknown"
