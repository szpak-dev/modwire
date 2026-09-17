from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from ....architecture.boundaries.models.flow_report import FlowReport
from ..domain import ReportPipelineStep
from ..models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="30-flow-violations")
@dataclass(frozen=True)
class FlowViolations(ReportPipelineStep):
    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return bool(context.report(FlowReport).violations)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(FlowReport)
        self.console.print("[red]Flow violations:[/red]")
        for violation in report.violations:
            self.console.print(f"  - [{violation.rule_name}] {violation.message}", markup=False)
            self.console.print(f"    {' -> '.join(violation.path)}", markup=False)
        return context.fail()
