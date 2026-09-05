from modwire.architecture.insights.models.clusters_report_item import ClustersReportItem
from modwire.architecture.report.models.report_item import ReportItem


class ClustersReport(ReportItem):
    report_id: str = "architecture.insights.clusters"
    report_title: str = "Dependency Clusters"
    report_description: str = (
        "Groups source files into path-based clusters and ranks them by incoming and outgoing dependency pressure."
    )
    report_path: str = "insights.clusters"
    report_order: int = 10
    clusters: tuple[ClustersReportItem, ...] = ()
