from pydantic import Field

from .configuration_value import ConfigurationValue
from .shape_rules import ShapeRules


class ShapeRealm(ConfigurationValue):
    name: str = Field(min_length=1)
    match: str = Field(min_length=1)
    excluded_patterns: tuple[str, ...] = ()
    shape: ShapeRules = Field(default_factory=ShapeRules)
