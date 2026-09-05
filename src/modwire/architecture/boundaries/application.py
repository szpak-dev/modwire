from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.boundaries.models.flow_report import FlowReport
from modwire.architecture.boundaries.services.boundaries_flow_analyzer import BoundariesFlowAnalyzer
from modwire.architecture.config.application import ConfigApplication
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.report.domain import ReportCollector


@injectable(as_type=ReportCollector, qualifier="boundaries")
@dataclass(frozen=True)
class BoundariesApplication(ReportCollector):
    flow_analyzer: BoundariesFlowAnalyzer
    config: ConfigApplication

    @property
    def report_type(self) -> type[FlowReport]:
        return FlowReport

    def collect(self, architecture_map: ArchitectureMap) -> FlowReport:
        return self.report_type(
            violations=self.flow_analyzer.analyze(architecture_map, self.config.boundaries),
            analyzers=self.flow_analyzer.analyzer_names(self.config.boundaries),
        )
