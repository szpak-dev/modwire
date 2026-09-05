from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from modwire.architecture.insights.models.hotspots_report import HotspotsReport
from modwire.cli.pipeline.domain import ReportPipelineStep
from modwire.cli.pipeline.models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="60-hotspots")
@dataclass(frozen=True)
class HotspotsInsight(ReportPipelineStep):
    """Render dependency hotspots when the report identifies them."""

    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return context.has_report(HotspotsReport) and bool(context.report(HotspotsReport).hotspots)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(HotspotsReport)
        self.console.print("[blue]Dependency hotspots:[/blue]")
        for hotspot in report.hotspots:
            self.console.print(
                f"  - {hotspot.source_id} (pressure: {hotspot.pressure_score}, "
                f"incoming: {hotspot.incoming_count}, outgoing: {hotspot.outgoing_count})",
                markup=False,
            )
        return context
