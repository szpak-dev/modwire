from collections.abc import Sequence
from dataclasses import dataclass

from wireup import injectable

from ..config.models.architecture_config import ArchitectureConfig
from ..map.models.architecture_map import ArchitectureMap
from ..report.domain import ReportCollector
from ..report.models.report_item import ReportItem
from .domain import InsightReporterInterface
from .models.insight_report import InsightReport
from .services.insight_report_field_map import InsightReportFieldMap


@injectable(as_type=ReportCollector, qualifier="insights")
@dataclass(frozen=True)
class InsightsApplication(ReportCollector):
    @property
    def report_type(self) -> type[InsightReport]:
        return InsightReport

    reporters: Sequence[InsightReporterInterface]
    field_map: InsightReportFieldMap

    def _field_for(self, name: str):
        return self.field_map.field_for(name)

    def collect(self, architecture_map: ArchitectureMap, config: ArchitectureConfig) -> InsightReport:
        payload: dict[str, ReportItem] = {}
        for reporter in self.reporters:
            name = reporter.name
            field = self._field_for(name)
            payload[field] = reporter.collect(architecture_map)
        return self.report_type.model_validate(payload)
