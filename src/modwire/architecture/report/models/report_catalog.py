from ....shared.values.models.value_model import ValueModel
from .report_metadata import ReportMetadata


class ReportCatalog(ValueModel):
    reports: tuple[ReportMetadata, ...]
