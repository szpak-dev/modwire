from dataclasses import dataclass

from rich.console import Console
from wireup import injectable

from ....architecture.insights.models.clusters_report import ClustersReport
from ..domain import ReportPipelineStep
from ..models.report_pipeline_context import ReportPipelineContext


@injectable(as_type=ReportPipelineStep, qualifier="50-clusters")
@dataclass(frozen=True)
class ClustersInsight(ReportPipelineStep):
    """Render dependency clusters when the report identifies them."""

    console: Console

    def should_process(self, context: ReportPipelineContext) -> bool:
        return context.has_report(ClustersReport) and bool(context.report(ClustersReport).clusters)

    def process(self, context: ReportPipelineContext) -> ReportPipelineContext:
        report = context.report(ClustersReport)
        self.console.print("[blue]Dependency clusters:[/blue]")
        for cluster in report.clusters:
            self.console.print(
                f"{cluster.name} (pressure: {cluster.pressure_score}, "
                f"incoming: {cluster.incoming_count}, outgoing: {cluster.outgoing_count})",
                markup=False,
            )
            for source_id in cluster.top_files:
                self.console.print(f"  - {source_id}", markup=False)
        return context
