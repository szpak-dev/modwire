from collections.abc import Sequence
from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.map.application import MapApplication
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap

from .domain import ReportCollector
from .models.report_catalog import ReportCatalog
from .models.report_descriptor import ReportDescriptor
from .models.report_node import ReportNode


@injectable
@dataclass(frozen=True)
class ReportApplication:
    maps: MapApplication
    collectors: Sequence[ReportCollector]

    def reports(self) -> ReportCatalog:
        reports = (ReportDescriptor(report_type=collector.report_type).metadata() for collector in self.collectors)
        return ReportCatalog(reports=tuple(sorted(reports, key=lambda item: (item.order, item.id))))

    def report(self, code_map: QueryableCodeMap) -> tuple[ReportNode, ...]:
        architecture_map = self.maps.load(code_map)
        reports = (collector.collect(architecture_map) for collector in self.collectors)
        return tuple(sorted(reports, key=lambda item: (item.metadata.order, item.metadata.id)))
