from modwire.architecture.insights.models.hotspots_report_item import HotspotsReportItem
from modwire.architecture.report.models.report_item import ReportItem


class HotspotsReport(ReportItem):
    report_id: str = "architecture.insights.hotspots"
    report_title: str = "Dependency Hotspots"
    report_description: str = (
        "Ranks source files by dependency pressure from their incoming and outgoing dependency counts."
    )
    report_path: str = "insights.hotspots"
    report_order: int = 20
    hotspots: tuple[HotspotsReportItem, ...] = ()
