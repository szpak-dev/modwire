from enum import StrEnum


class SourceParameterKind(StrEnum):
    POSITIONAL = "positional"
    VARIADIC_POSITIONAL = "variadic_positional"
    NAMED_ONLY = "named_only"
    VARIADIC_NAMED = "variadic_named"
