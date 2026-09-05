import abc

from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.report.models.report_item import ReportItem


class InsightReporterInterface(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def report_type(self) -> type[ReportItem]:
        raise NotImplementedError

    @abc.abstractmethod
    def collect(self, architecture_map: ArchitectureMap) -> ReportItem:
        raise NotImplementedError
