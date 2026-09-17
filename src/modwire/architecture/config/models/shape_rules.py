from pydantic import Field

from .configuration_value import ConfigurationValue


class ShapeRules(ConfigurationValue):
    max_classes_per_file: int = Field(default=-1, ge=-1)
    max_interfaces_per_file: int = Field(default=-1, ge=-1)
    max_types_per_file: int = Field(default=-1, ge=-1)
    max_abstract_classes_per_file: int = Field(default=-1, ge=-1)
    max_functions_per_file: int = Field(default=0, ge=-1)
    max_methods_per_class: int = Field(default=-1, ge=-1)
    max_declared_args: int = Field(default=-1, ge=-1)
    max_function_lines: int = Field(default=-1, ge=-1)
    max_method_lines: int = Field(default=-1, ge=-1)
    max_class_lines: int = Field(default=-1, ge=-1)
    allow_optional_function_args: bool = False
    allow_optional_method_args: bool = False
    allow_optional_class_properties: bool = False
    allow_import_aliases: bool = False
    require_joined_imports: bool = True
    allowed_import_crossing_types: tuple[str, ...] = ("module", "symbol")
