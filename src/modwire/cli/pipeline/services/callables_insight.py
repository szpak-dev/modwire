from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from ....architecture.insights.models.callables_report import CallablesReport
from ..domain import ReportPipelineStep
from ..models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="80-callables")
@dataclass(frozen=True)
class CallablesInsight(ReportPipelineStep):
    """Render callable graph entries when the report has relationships."""

    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return context.has_report(CallablesReport) and bool(context.report(CallablesReport).entries)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(CallablesReport)
        self.console.print("[blue]Callable graph:[/blue]")
        for entry in report.entries:
            self.console.print(entry.source_callable, markup=False)
            for call in entry.calls:
                self.console.print(f"  calls: {call}", markup=False)
            for caller in entry.callers:
                self.console.print(f"  called by: {caller}", markup=False)
        return context
