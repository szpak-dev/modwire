from enum import StrEnum


class SourceCallableKind(StrEnum):
    FUNCTION = "function"
    INSTANCE_METHOD = "instance_method"
    TYPE_METHOD = "type_method"
    STATIC_METHOD = "static_method"
    CONSTRUCTOR = "constructor"
    CALLABLE_VALUE = "callable_value"
    ANONYMOUS = "anonymous"
