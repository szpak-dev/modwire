from modwire.architecture.report.models.architecture_group import ArchitectureGroup
from modwire.architecture.report.models.report_item import ReportItem


class MapReport(ReportItem):
    report_id: str = "architecture.map"
    report_title: str = "Architecture Map"
    report_description: str = (
        "Groups source files by configured architecture modules and layers, and lists files "
        "that were not matched by the architecture map."
    )
    report_path: str = "map"
    report_order: int = 10
    modules: tuple[ArchitectureGroup, ...] = ()
    layers: tuple[ArchitectureGroup, ...] = ()
    unknown_files: tuple[str, ...] = ()
