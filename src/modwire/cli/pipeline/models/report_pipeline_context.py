from typing import cast

from ....architecture.report.models.report_node import ReportNode
from ....shared.values.models.value_model import ValueModel


class ReportPipelineContext(ValueModel):
    """Carry report data and rendering state through the report pipeline."""

    reports: tuple[ReportNode, ...]
    summary: bool = False
    failed: bool = False

    def has_report(self, report_type: type[ReportNode]) -> bool:
        return any(type(report) is report_type for report in self.reports)

    def report[ReportType: ReportNode](self, report_type: type[ReportType]) -> ReportType:
        for report in self.reports:
            if type(report) is report_type:
                return cast(ReportType, report)
        raise LookupError(f"Missing report: {report_type.__name__}")

    def fail(self) -> "ReportPipelineContext":
        return self.model_copy(update={"failed": True})
