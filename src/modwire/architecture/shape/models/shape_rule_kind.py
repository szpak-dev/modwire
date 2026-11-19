from enum import StrEnum


class ShapeRuleKind(StrEnum):
    MAX_CLASSES_PER_FILE = "max_classes_per_file"
    MAX_INTERFACES_PER_FILE = "max_interfaces_per_file"
    MAX_TYPES_PER_FILE = "max_types_per_file"
    MAX_ABSTRACT_CLASSES_PER_FILE = "max_abstract_classes_per_file"
    MAX_FUNCTIONS_PER_FILE = "max_functions_per_file"
    MAX_VARIABLES_PER_FILE = "max_variables_per_file"
    MAX_METHODS_PER_CLASS = "max_methods_per_class"
    MAX_DECLARED_ARGS = "max_declared_args"
    MAX_FUNCTION_LINES = "max_function_lines"
    MAX_METHOD_LINES = "max_method_lines"
    MAX_CLASS_LINES = "max_class_lines"
    ALLOW_OPTIONAL_FUNCTION_ARGS = "allow_optional_function_args"
    ALLOW_OPTIONAL_METHOD_ARGS = "allow_optional_method_args"
    ALLOW_OPTIONAL_CLASS_PROPERTIES = "allow_optional_class_properties"
    ALLOW_IMPORT_ALIASES = "allow_import_aliases"
    REQUIRE_JOINED_IMPORTS = "require_joined_imports"
    ALLOWED_IMPORT_CROSSING_TYPES = "allowed_import_crossing_types"
