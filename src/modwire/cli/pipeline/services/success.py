from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from modwire.cli.pipeline.domain import ReportPipelineStep
from modwire.cli.pipeline.models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="100-success")
@dataclass(frozen=True)
class Success(ReportPipelineStep):
    """Render the successful architecture-check result."""

    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return not context.failed

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        self.console.print("[green]Architecture checks passed.[/green]")
        return context
