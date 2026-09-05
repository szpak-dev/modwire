from collections.abc import Sequence
from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.insights.domain import InsightReporterInterface
from modwire.architecture.insights.models.insight_report import InsightReport
from modwire.architecture.insights.services.insight_report_field_map import InsightReportFieldMap
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.report.domain import ReportCollector
from modwire.architecture.report.models.report_item import ReportItem


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

    def collect(self, architecture_map: ArchitectureMap) -> InsightReport:
        payload: dict[str, ReportItem] = {}
        for reporter in self.reporters:
            name = reporter.name
            field = self._field_for(name)
            payload[field] = reporter.collect(architecture_map)
        return self.report_type.model_validate(payload)
