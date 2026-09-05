from ...report.models.report_item import ReportItem
from .callable_report_entry import CallableReportEntry


class CallablesReport(ReportItem):
    report_id: str = "architecture.insights.callables"
    report_title: str = "Callable Graph"
    report_description: str = (
        "Lists callable-level call relationships, including calls made by each callable and callers that reference it."
    )
    report_path: str = "insights.callables"
    report_order: int = 40
    entries: tuple[CallableReportEntry, ...] = ()
