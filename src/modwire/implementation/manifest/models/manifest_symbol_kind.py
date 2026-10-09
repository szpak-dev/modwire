from enum import StrEnum


class ManifestSymbolKind(StrEnum):
    CLASS = "class"
    ABSTRACT_CLASS = "abstract_class"
    INTERFACE = "interface"
    TYPE = "type"
    FUNCTION = "function"
    CALLABLE = "callable"
    CALLABLE_VALUE = "value:callable"
    CLASS_VALUE = "value:class"
    LITERAL_VALUE = "value:literal"
    OBJECT_VALUE = "value:object"
    UNKNOWN_VALUE = "value:unknown"
