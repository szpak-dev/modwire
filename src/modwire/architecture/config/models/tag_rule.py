from pydantic import Field

from modwire.architecture.config.models.configuration_value import ConfigurationValue


class TagRule(ConfigurationValue):
    name: str = Field(min_length=1)
    match: str = Field(min_length=1)
    excluded_patterns: tuple[str, ...] = ()
