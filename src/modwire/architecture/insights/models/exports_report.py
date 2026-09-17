from ...report.models.report_item import ReportItem
from .exports_report_item import ExportsReportItem


class ExportsReport(ReportItem):
    report_id: str = "architecture.insights.exports"
    report_title: str = "Unused Exports"
    report_description: str = "Lists exported symbols that are not referenced by tracked imports."
    report_path: str = "insights.exports"
    report_order: int = 50
    unused_exports: tuple[ExportsReportItem, ...] = ()
