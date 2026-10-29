from abc import ABC, abstractmethod

from ...shared.code.models.queryable_code_map import QueryableCodeMap
from ..config.models.boundaries_config import BoundariesConfig
from .models.architecture_map import ArchitectureMap


class ArchitectureMapper(ABC):
    @abstractmethod
    def load(self, code_map: QueryableCodeMap, config: BoundariesConfig) -> ArchitectureMap:
        raise NotImplementedError
