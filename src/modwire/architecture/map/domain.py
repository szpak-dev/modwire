from abc import ABC, abstractmethod

from modwire.architecture.config.models.boundaries_config import BoundariesConfig
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap

from .models.architecture_map import ArchitectureMap


class ArchitectureMapper(ABC):
    @abstractmethod
    def load(self, code_map: QueryableCodeMap, config: BoundariesConfig) -> ArchitectureMap:
        raise NotImplementedError
