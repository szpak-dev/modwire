from enum import StrEnum


class ShapeSymbolKind(StrEnum):
    ABSTRACT_CLASS = "abstract_class"
    ABSTRACT_CLASS_PROPERTY = "abstract_class_property"
    CLASS = "class"
    CLASS_PROPERTY = "class_property"
    FILE = "file"
    FUNCTION = "function"
    IMPORT = "import"
    INTERFACE = "interface"
    INTERFACE_PROPERTY = "interface_property"
    METHOD = "method"
    SIGNATURE = "signature"
    TYPE = "type"
    TYPE_PROPERTY = "type_property"
