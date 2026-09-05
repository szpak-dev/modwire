from modwire.architecture.boundaries.models.flow_violation import FlowViolation
from modwire.architecture.report.models.report_item import ReportItem


class FlowReport(ReportItem):
    report_id: str = "architecture.violations.flow"
    report_title: str = "Dependency Flow"
    report_description: str = (
        "Reports dependency-flow violations such as backward dependencies, cycles, and "
        "forbidden re-entry between configured architecture realms."
    )
    report_path: str = "violations.flow"
    report_order: int = 10
    violations: tuple[FlowViolation, ...] = ()
    analyzers: tuple[str, ...] = ()
