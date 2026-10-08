from dataclasses import dataclass
from typing import ClassVar

from wireup import injectable

from ....shared.code.models.identity import FileId
from ...map.models.architecture_map import ArchitectureMap
from ..domain import InsightReporterInterface
from ..models.clusters_report import ClustersReport
from ..models.clusters_report_item import ClustersReportItem


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
        tracked_source_ids = set(source_ids)
        file_sets: dict[str, list[str]] = {}
        cluster_by_source_id: dict[str, str] = {}
        for source_id in source_ids:
            cluster_name = self.cluster_name(source_id)
            file_sets.setdefault(cluster_name, []).append(source_id)
            cluster_by_source_id[source_id] = cluster_name

        incoming_by_cluster = dict.fromkeys(file_sets, 0)
        outgoing_by_cluster = dict.fromkeys(file_sets, 0)
        pressure_by_file: dict[str, int] = dict.fromkeys(source_ids, 0)
        for edge in architecture_map.code_map.cm.dependency_graph.edges:
            if edge.from_id in tracked_source_ids:
                pressure_by_file[edge.from_id] += 1
            if edge.to_id is None or edge.to_id not in tracked_source_ids:
                continue

            pressure_by_file[edge.to_id] += 1
            target_cluster = cluster_by_source_id[edge.to_id]
            source_cluster = cluster_by_source_id.get(edge.from_id)
            if source_cluster == target_cluster:
                continue
            incoming_by_cluster[target_cluster] += 1
            if source_cluster is not None:
                outgoing_by_cluster[source_cluster] += 1

        clusters: list[ClustersReportItem] = []
        for name, files in sorted(file_sets.items()):
            file_tuple = tuple(sorted(files))
            incoming_count = incoming_by_cluster[name]
            outgoing_count = outgoing_by_cluster[name]
            clusters.append(
                ClustersReportItem(
                    name=name,
                    files=file_tuple,
                    incoming_count=incoming_count,
                    outgoing_count=outgoing_count,
                    pressure_score=incoming_count + outgoing_count,
                    top_files=tuple(
                        sorted(files, key=lambda source_id: (-pressure_by_file[source_id], source_id))[
                            : self.top_file_limit
                        ]
                    ),
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
        graph = architecture_map.code_map.cm.dependency_graph
        return len(graph.incoming(FileId(source_id))) + len(graph.outgoing(FileId(source_id)))
