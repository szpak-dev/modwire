from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import FileId
from ....shared.code.models.source_dependency_resolution import SourceDependencyResolution
from ...map.models.architecture_map import ArchitectureMap
from ..domain import InsightReporterInterface
from ..models.coherence_report import CoherenceReport


@injectable(as_type=InsightReporterInterface, qualifier="coherence")
@dataclass(frozen=True)
class CoherenceReporter(InsightReporterInterface):
    @property
    def name(self) -> str:
        return "coherence"

    @property
    def report_type(self) -> type[CoherenceReport]:
        return CoherenceReport

    def collect(self, architecture_map: ArchitectureMap) -> CoherenceReport:
        source_ids = set(architecture_map.code_map.source_ids())
        graph = architecture_map.code_map.cm.dependency_graph
        roots: list[str] = []
        leaves: list[str] = []
        isolated: list[str] = []
        for source_id in sorted(source_ids):
            has_incoming = len(graph.incoming(FileId(source_id))) > 0
            has_outgoing = len(graph.outgoing(FileId(source_id))) > 0
            if not has_incoming:
                roots.append(source_id)
            if not has_outgoing:
                leaves.append(source_id)
            if not has_incoming and (not has_outgoing):
                isolated.append(source_id)
        external_dependencies = {
            edge.specifier
            for edge in graph.external_edges(source_ids)
            if edge.resolution is SourceDependencyResolution.EXTERNAL
        }
        return self.report_type(
            roots=tuple(roots),
            leaves=tuple(leaves),
            isolated=tuple(isolated),
            external_dependencies=tuple(sorted(external_dependencies)),
        )
