from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.insights.domain import InsightReporterInterface
from modwire.architecture.insights.models.coherence_report import CoherenceReport
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.shared.code.models.identity import FileId


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
        roots: list[str] = []
        leaves: list[str] = []
        isolated: list[str] = []
        for source_id in sorted(source_ids):
            has_incoming = architecture_map.code_map.incoming_dependencies(FileId(source_id)).count() > 0
            has_outgoing = architecture_map.code_map.outgoing_dependencies(FileId(source_id)).count() > 0
            if not has_incoming:
                roots.append(source_id)
            if not has_outgoing:
                leaves.append(source_id)
            if not has_incoming and (not has_outgoing):
                isolated.append(source_id)
        external_dependencies = {
            edge_result.edge.specifier
            for edge_result in architecture_map.code_map.external_dependency_edges().all()
            if edge_result.edge.resolution == "external"
        }
        return self.report_type(
            roots=tuple(roots),
            leaves=tuple(leaves),
            isolated=tuple(isolated),
            external_dependencies=tuple(sorted(external_dependencies)),
        )
