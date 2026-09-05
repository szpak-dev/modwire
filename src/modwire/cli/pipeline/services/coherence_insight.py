from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from modwire.architecture.insights.models.coherence_report import CoherenceReport
from modwire.cli.pipeline.domain import ReportPipelineStep
from modwire.cli.pipeline.models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="70-coherence")
@dataclass(frozen=True)
class CoherenceInsight(ReportPipelineStep):
    """Render roots, leaves, isolated nodes, and external dependencies."""

    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        if not context.has_report(CoherenceReport):
            return False
        report = context.report(CoherenceReport)
        return bool(report.roots or report.leaves or report.isolated or report.external_dependencies)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(CoherenceReport)
        self.console.print("[blue]Dependency coherence:[/blue]")
        self._print_section(context, "Roots", report.roots)
        self._print_section(context, "Leaves", report.leaves)
        self._print_section(context, "Isolated", report.isolated)
        self._print_section(context, "External dependencies", report.external_dependencies)
        return context

    def _print_section(self, context: ReportPipelineContext, title: str, entries: tuple[str, ...]) -> None:
        if not entries:
            return
        self.console.print(title)
        for entry in entries:
            self.console.print(f"  - {entry}", markup=False)
