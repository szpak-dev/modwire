from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.report.domain import ReportCollector
from modwire.architecture.report.models.architecture_group import ArchitectureGroup
from modwire.architecture.report.models.map_report import MapReport


@injectable(as_type=ReportCollector, qualifier="map")
@dataclass(frozen=True)
class MapReportCollector(ReportCollector):
    @property
    def report_type(self) -> type[MapReport]:
        return MapReport

    def collect(self, architecture_map: ArchitectureMap) -> MapReport:
        return self.report_type(
            modules=tuple(
                (
                    ArchitectureGroup(name=name, source_ids=source_ids)
                    for name, source_ids in sorted(architecture_map.modules.items())
                )
            ),
            layers=tuple(
                (
                    ArchitectureGroup(name=name, source_ids=source_ids)
                    for name, source_ids in sorted(architecture_map.layers.items())
                )
            ),
            unknown_files=architecture_map.unknown_files,
        )
