from pydantic import Field

from modwire.architecture.config.models.boundaries_config import BoundariesConfig
from modwire.architecture.config.models.configuration_value import ConfigurationValue
from modwire.architecture.config.models.shape_config import ShapeConfig


class ArchitectureConfig(ConfigurationValue):
    excluded_patterns: tuple[str, ...] = ()
    boundaries: BoundariesConfig = Field(default_factory=BoundariesConfig)
    shape: ShapeConfig
