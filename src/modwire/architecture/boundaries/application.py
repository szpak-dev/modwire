from dataclasses import dataclass

from wireup import injectable

from ..config.models.architecture_config import ArchitectureConfig
from ..map.models.architecture_map import ArchitectureMap
from ..report.domain import ReportCollector
from .models.flow_report import FlowReport
from .services.boundaries_flow_analyzer import BoundariesFlowAnalyzer


@injectable(as_type=ReportCollector, qualifier="boundaries")
@dataclass(frozen=True)
class BoundariesApplication(ReportCollector):
    flow_analyzer: BoundariesFlowAnalyzer

    @property
    def report_type(self) -> type[FlowReport]:
        return FlowReport

    def collect(self, architecture_map: ArchitectureMap, config: ArchitectureConfig) -> FlowReport:
        return self.report_type(
            violations=self.flow_analyzer.analyze(architecture_map, config.boundaries),
            analyzers=self.flow_analyzer.analyzer_names(config.boundaries),
        )
