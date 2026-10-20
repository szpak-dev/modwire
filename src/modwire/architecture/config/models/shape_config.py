from pydantic import Field, model_validator

from .architecture_config_validation_error import ArchitectureConfigValidationError
from .architecture_config_violation import ArchitectureConfigViolation
from .configuration_value import ConfigurationValue
from .shape_realm import ShapeRealm


class ShapeConfig(ConfigurationValue):
    realms: tuple[ShapeRealm, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_realms(self) -> "ShapeConfig":
        names = tuple(realm.name for realm in self.realms)
        if len(names) != len(set(names)):
            raise ArchitectureConfigValidationError(ArchitectureConfigViolation.DUPLICATE_SHAPE_REALM, ", ".join(names))
        return self
