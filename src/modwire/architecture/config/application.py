from collections.abc import Mapping
from dataclasses import dataclass

from wireup import injectable

from .models.architecture_config import ArchitectureConfig


@injectable
@dataclass(frozen=True)
class ConfigApplication:
    def validate(self, values: Mapping[str, object]) -> ArchitectureConfig:
        return ArchitectureConfig.model_validate(values)
