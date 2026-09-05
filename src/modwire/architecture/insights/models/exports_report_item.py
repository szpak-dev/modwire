from modwire.shared.values.models.value_model import ValueModel


class ExportsReportItem(ValueModel):
    source_id: str
    name: str
    kind: str
    crossing_type: str
    reason: str
