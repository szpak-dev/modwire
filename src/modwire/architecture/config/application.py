from dataclasses import dataclass
from typing import Annotated

from wireup import Inject, injectable

from .models.architecture_config import ArchitectureConfig
from .models.boundaries_config import BoundariesConfig
from .models.shape_config import ShapeConfig


@injectable
@dataclass(frozen=True)
class ConfigApplication:
    configuration: Annotated[ArchitectureConfig | None, Inject(config="architecture")]

    def current(self) -> ArchitectureConfig:
        if self.configuration is None:
            raise ValueError("Architecture services require an explicit runtime configuration.")
        return self.configuration

    @property
    def boundaries(self) -> BoundariesConfig:
        return self.current().boundaries

    @property
    def shape(self) -> ShapeConfig:
        return self.current().shape
