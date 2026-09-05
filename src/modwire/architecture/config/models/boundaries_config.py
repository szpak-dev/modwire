from pydantic import Field, model_validator

from modwire.architecture.config.models.boundary_rule import BoundaryRule
from modwire.architecture.config.models.configuration_value import ConfigurationValue
from modwire.architecture.config.models.flow_rules import FlowRules
from modwire.architecture.config.models.tag_rule import TagRule


class BoundariesConfig(ConfigurationValue):
    tags: tuple[TagRule, ...] = ()
    rules: tuple[BoundaryRule, ...] = ()
    flow: FlowRules = Field(default_factory=FlowRules)

    @model_validator(mode="after")
    def unique_tag_names(self) -> "BoundariesConfig":
        names = tuple(tag.name for tag in self.tags)
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError("Architecture tag names must be unique: " + ", ".join(duplicates))
        return self

    @model_validator(mode="after")
    def known_rule_realms(self) -> "BoundariesConfig":
        realms = {realm.name for realm in self.flow.realms}
        unknown = sorted({rule.realm for rule in self.rules if rule.realm and rule.realm not in realms})
        if unknown:
            raise ValueError("Unknown boundary rule realms: " + ", ".join(unknown))
        return self
