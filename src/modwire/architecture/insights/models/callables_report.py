from modwire.architecture.insights.models.callable_report_entry import CallableReportEntry
from modwire.architecture.report.models.report_item import ReportItem


class CallablesReport(ReportItem):
    report_id: str = "architecture.insights.callables"
    report_title: str = "Callable Graph"
    report_description: str = (
        "Lists callable-level call relationships, including calls made by each callable and callers that reference it."
    )
    report_path: str = "insights.callables"
    report_order: int = 40
    entries: tuple[CallableReportEntry, ...] = ()
