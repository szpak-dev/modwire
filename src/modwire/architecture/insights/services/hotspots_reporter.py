from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import FileId
from ...map.models.architecture_map import ArchitectureMap
from ..domain import InsightReporterInterface
from ..models.hotspots_report import HotspotsReport
from ..models.hotspots_report_item import HotspotsReportItem


@injectable(as_type=InsightReporterInterface, qualifier="hotspots")
@dataclass(frozen=True)
class HotspotsReporter(InsightReporterInterface):
    @property
    def name(self) -> str:
        return "hotspots"

    @property
    def report_type(self) -> type[HotspotsReport]:
        return HotspotsReport

    def collect(self, architecture_map: ArchitectureMap) -> HotspotsReport:
        hotspots = tuple(
            sorted(
                (self.hotspot_for(architecture_map, source_id) for source_id in architecture_map.code_map.source_ids()),
                key=lambda hotspot: (-hotspot.pressure_score, hotspot.source_id),
            )
        )
        return self.report_type(hotspots=hotspots)

    def hotspot_for(self, architecture_map: ArchitectureMap, source_id: str) -> HotspotsReportItem:
        incoming_count = architecture_map.code_map.incoming_dependencies(FileId(source_id)).count()
        outgoing_count = architecture_map.code_map.outgoing_dependencies(FileId(source_id)).count()
        return HotspotsReportItem(
            source_id=source_id,
            incoming_count=incoming_count,
            outgoing_count=outgoing_count,
            pressure_score=incoming_count + outgoing_count,
        )
