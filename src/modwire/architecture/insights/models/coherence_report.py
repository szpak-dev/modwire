from modwire.architecture.report.models.report_item import ReportItem


class CoherenceReport(ReportItem):
    report_id: str = "architecture.insights.coherence"
    report_title: str = "Dependency Coherence"
    report_description: str = (
        "Summarizes graph coherence by listing roots, leaves, isolated files, and external dependency endpoints."
    )
    report_path: str = "insights.coherence"
    report_order: int = 30
    roots: tuple[str, ...] = ()
    leaves: tuple[str, ...] = ()
    isolated: tuple[str, ...] = ()
    external_dependencies: tuple[str, ...] = ()
