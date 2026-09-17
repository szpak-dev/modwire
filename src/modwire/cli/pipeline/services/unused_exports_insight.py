from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from ....architecture.insights.models.exports_report import ExportsReport
from ..domain import ReportPipelineStep
from ..models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="90-unused-exports")
@dataclass(frozen=True)
class UnusedExportsInsight(ReportPipelineStep):
    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return context.has_report(ExportsReport) and bool(context.report(ExportsReport).unused_exports)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(ExportsReport)
        self.console.print("[blue]Unused exports:[/blue]")
        for export in report.unused_exports:
            self.console.print(
                f"  - {export.source_id}: {export.kind} {export.name} ({export.crossing_type}; {export.reason})",
                markup=False,
            )
        return context
