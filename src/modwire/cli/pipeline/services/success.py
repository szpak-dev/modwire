from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from ..domain import ReportPipelineStep
from ..models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="100-success")
@dataclass(frozen=True)
class Success(ReportPipelineStep):
    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return not context.failed

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        self.console.print("[green]Architecture checks passed.[/green]")
        return context
