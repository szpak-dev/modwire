from enum import StrEnum


class PythonTraversalRole(StrEnum):
    MODULE = "module"
    MODULE_CLASS = "module_class"
    NESTED_CLASS = "nested_class"
    NESTED = "nested"
