from modwire.architecture.report.models.report_item import ReportItem
from modwire.architecture.shape.models.shape_violation import ShapeViolation


class ShapeReport(ReportItem):
    report_id: str = "architecture.violations.shape"
    report_title: str = "Shape Violations"
    report_description: str = (
        "Reports source-shape violations detected by configured resolvers, including file, "
        "class, callable, import, property, signature, and symbol rules."
    )
    report_path: str = "violations.shape"
    report_order: int = 20
    violations: tuple[ShapeViolation, ...] = ()
    resolvers: tuple[str, ...] = ()
