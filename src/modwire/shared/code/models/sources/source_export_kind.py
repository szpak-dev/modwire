from enum import StrEnum


class SourceExportKind(StrEnum):
    MODULE = "module"
    CLASS = "class"
    INTERFACE = "interface"
    TYPE = "type"
    ABSTRACT_CLASS = "abstract_class"
    FUNCTION = "function"
    VALUE = "value"
    UNKNOWN = "unknown"
