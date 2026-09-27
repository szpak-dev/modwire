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
    INHERITANCE = "inheritance"
    DEPENDENCIES = "dependencies"
    SPANS = "spans"
