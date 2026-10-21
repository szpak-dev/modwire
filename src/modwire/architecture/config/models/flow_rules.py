from pydantic import model_validator

from .architecture_config_validation_error import ArchitectureConfigValidationError
from .architecture_config_violation import ArchitectureConfigViolation
from .configuration_value import ConfigurationValue
from .flow_realm import FlowRealm


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
            raise ArchitectureConfigValidationError(ArchitectureConfigViolation.DUPLICATE_FLOW_REALM, ", ".join(names))
        if len(self.analyzers) != len(set(self.analyzers)):
            raise ArchitectureConfigValidationError(
                ArchitectureConfigViolation.DUPLICATE_FLOW_ANALYZER, ", ".join(self.analyzers)
            )
        return self
