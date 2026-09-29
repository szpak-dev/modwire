from enum import StrEnum


class FactCapability(StrEnum):
    """Versioned implementation fact families that an extractor can publish."""

    SOURCES = "sources"
    SYMBOLS = "symbols"
    CALLABLES = "callables"
    PARAMETERS = "parameters"
    ANNOTATIONS = "annotations"
    MODIFIERS = "modifiers"
    ATTRIBUTES = "attributes"
    ASSIGNED_VALUES = "assigned_values"
    INHERITANCE = "inheritance"
    DEPENDENCIES = "dependencies"
    SPANS = "spans"
