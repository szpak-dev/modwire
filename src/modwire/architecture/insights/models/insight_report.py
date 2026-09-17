from pydantic import Field

from ...report.models.report_node import ReportNode
from ...report.models.report_section import ReportSection
from .callables_report import CallablesReport
from .clusters_report import ClustersReport
from .coherence_report import CoherenceReport
from .exports_report import ExportsReport
from .hotspots_report import HotspotsReport


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
