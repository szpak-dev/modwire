from modwire.architecture.report.models.report_metadata import ReportMetadata
from modwire.shared.values.models.value_model import ValueModel


class ReportCatalog(ValueModel):
    reports: tuple[ReportMetadata, ...]
