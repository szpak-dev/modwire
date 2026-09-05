from dataclasses import dataclass
from typing import ClassVar

from wireup import injectable

from modwire.architecture.insights.domain import InsightReporterInterface
from modwire.architecture.insights.models.clusters_report import ClustersReport
from modwire.architecture.insights.models.clusters_report_item import ClustersReportItem
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.shared.code.models.identity import FileId


@injectable(as_type=InsightReporterInterface, qualifier="clusters")
@dataclass(frozen=True)
class ClustersReporter(InsightReporterInterface):
    @property
    def name(self) -> str:
        return "clusters"

    @property
    def report_type(self) -> type[ClustersReport]:
        return ClustersReport

    group_depth: ClassVar[int] = 2
    top_file_limit: ClassVar[int] = 5

    def collect(self, architecture_map: ArchitectureMap) -> ClustersReport:
        source_ids = architecture_map.code_map.source_ids()
        file_sets: dict[str, list[str]] = {}
        for source_id in source_ids:
            file_sets.setdefault(self.cluster_name(source_id), []).append(source_id)
        clusters: list[ClustersReportItem] = []
        for name, files in sorted(file_sets.items()):
            file_tuple = tuple(sorted(files))
            incoming_count = self.incoming_count(architecture_map, file_tuple)
            outgoing_count = self.outgoing_count(architecture_map, file_tuple)
            clusters.append(
                ClustersReportItem(
                    name=name,
                    files=file_tuple,
                    incoming_count=incoming_count,
                    outgoing_count=outgoing_count,
                    pressure_score=incoming_count + outgoing_count,
                    top_files=self.top_files(architecture_map, file_tuple),
                )
            )
        return self.report_type(
            clusters=tuple(sorted(clusters, key=lambda cluster: (-cluster.pressure_score, cluster.name)))
        )

    def cluster_name(self, source_id: str) -> str:
        parts = tuple(part for part in source_id.split("/") if part)
        if not parts:
            return source_id
        return "/".join(parts[: self.group_depth])

    def incoming_count(self, architecture_map: ArchitectureMap, files: tuple[str, ...]) -> int:
        file_set = set(files)
        return sum(
            1
            for dependency in architecture_map.code_map.tracked_dependency_edges().all()
            if dependency.edge.to_id in file_set and dependency.edge.from_id not in file_set
        )

    def outgoing_count(self, architecture_map: ArchitectureMap, files: tuple[str, ...]) -> int:
        file_set = set(files)
        return sum(
            1
            for dependency in architecture_map.code_map.tracked_dependency_edges().all()
            if dependency.edge.from_id in file_set and dependency.edge.to_id not in file_set
        )

    def top_files(self, architecture_map: ArchitectureMap, files: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(files, key=lambda source_id: (-self.file_pressure(architecture_map, source_id), source_id))[
                : self.top_file_limit
            ]
        )

    def file_pressure(self, architecture_map: ArchitectureMap, source_id: str) -> int:
        return (
            architecture_map.code_map.incoming_dependencies(FileId(source_id)).count()
            + architecture_map.code_map.outgoing_dependencies(FileId(source_id)).count()
        )
