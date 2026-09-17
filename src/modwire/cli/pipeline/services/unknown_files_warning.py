from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from ....architecture.report.models.map_report import MapReport
from ..domain import ReportPipelineStep
from ..models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="20-unknown-files")
@dataclass(frozen=True)
class UnknownFilesWarning(ReportPipelineStep):
    """Warn when source files are absent from the configured architecture map."""

    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return bool(context.report(MapReport).unknown_files)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(MapReport)
        self.console.print("[yellow]Warning:[/yellow] Files not included in the architecture map:")
        for source_id in report.unknown_files:
            self.console.print(f"  - {source_id}", markup=False)
        return context
