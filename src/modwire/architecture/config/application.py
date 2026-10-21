from collections.abc import Mapping
from dataclasses import dataclass

from pydantic import ValidationError
from wireup import injectable

from .models.architecture_config import ArchitectureConfig
from .models.architecture_config_validation_error import ArchitectureConfigValidationError
from .models.architecture_config_violation import ArchitectureConfigViolation


@injectable
@dataclass(frozen=True)
class ConfigApplication:
    def validate(self, values: Mapping[str, object]) -> ArchitectureConfig:
        try:
            return ArchitectureConfig.model_validate(values)
        except ValidationError as error:
            raise ArchitectureConfigValidationError(
                ArchitectureConfigViolation.INVALID_CONFIGURATION,
                "architecture configuration",
            ) from error
