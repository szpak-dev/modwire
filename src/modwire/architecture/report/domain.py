from abc import ABC, abstractmethod

from ..config.models.architecture_config import ArchitectureConfig
from ..map.models.architecture_map import ArchitectureMap
from .models.report_node import ReportNode


class ReportCollector(ABC):
    @property
    @abstractmethod
    def report_type(self) -> type[ReportNode]:
        raise NotImplementedError

    @abstractmethod
    def collect(self, architecture_map: ArchitectureMap, config: ArchitectureConfig) -> ReportNode:
        raise NotImplementedError
