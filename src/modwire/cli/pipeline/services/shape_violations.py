from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from ....architecture.shape.models.shape_report import ShapeReport
from ..domain import ReportPipelineStep
from ..models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="40-shape-violations")
@dataclass(frozen=True)
class ShapeViolations(ReportPipelineStep):
    """Render source-shape violations and mark the run as failed."""

    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return bool(context.report(ShapeReport).violations)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(ShapeReport)
        self.console.print("[red]Shape violations:[/red]")
        for violation in report.violations:
            symbol = f" {violation.symbol_kind} {violation.symbol_name}" if violation.symbol_kind else ""
            self.console.print(
                f"  - [{violation.rule_name}] {violation.source_id}{symbol}: "
                f"{violation.actual} exceeds {violation.limit}",
                markup=False,
            )
        return context.fail()
