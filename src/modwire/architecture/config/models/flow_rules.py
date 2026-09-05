from pydantic import model_validator

from modwire.architecture.config.models.configuration_value import ConfigurationValue
from modwire.architecture.config.models.flow_realm import FlowRealm


class FlowRules(ConfigurationValue):
    layers: tuple[str, ...] = ()
    module_tag: str = ""
    realms: tuple[FlowRealm, ...] = ()
    standalone_tags: tuple[str, ...] = ()
    analyzers: tuple[str, ...] = ()

    @model_validator(mode="after")
    def unique_realms(self) -> "FlowRules":
        names = tuple(realm.name for realm in self.realms if realm.name)
        if len(names) != len(set(names)):
            raise ValueError("Flow realm names must be unique")
        if len(self.analyzers) != len(set(self.analyzers)):
            raise ValueError("Flow analyzer names must be unique")
        return self
