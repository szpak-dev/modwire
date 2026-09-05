from pydantic import Field

from modwire.architecture.insights.models.callables_report import CallablesReport
from modwire.architecture.insights.models.clusters_report import ClustersReport
from modwire.architecture.insights.models.coherence_report import CoherenceReport
from modwire.architecture.insights.models.exports_report import ExportsReport
from modwire.architecture.insights.models.hotspots_report import HotspotsReport
from modwire.architecture.report.models.report_node import ReportNode
from modwire.architecture.report.models.report_section import ReportSection


class InsightReport(ReportSection):
    report_id: str = "architecture.insights"
    report_title: str = "Architecture Insights"
    report_description: str = (
        "Collects architecture insight reports for dependency clusters, hotspots, coherence, "
        "callable relationships, and unused exports."
    )
    report_path: str = "insights"
    report_order: int = 30
    report_children: tuple[type[ReportNode], ...] = Field(
        default=(ClustersReport, HotspotsReport, CoherenceReport, CallablesReport, ExportsReport), exclude=True
    )
    clusters: ClustersReport = Field(default_factory=ClustersReport)
    hotspots: HotspotsReport = Field(default_factory=HotspotsReport)
    coherence: CoherenceReport = Field(default_factory=CoherenceReport)
    callables: CallablesReport = Field(default_factory=CallablesReport)
    exports: ExportsReport = Field(default_factory=ExportsReport)
