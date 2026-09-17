from pydantic import Field

from .boundaries_config import BoundariesConfig
from .configuration_value import ConfigurationValue
from .shape_config import ShapeConfig


class ArchitectureConfig(ConfigurationValue):
    excluded_patterns: tuple[str, ...] = ()
    boundaries: BoundariesConfig = Field(default_factory=BoundariesConfig)
    shape: ShapeConfig
