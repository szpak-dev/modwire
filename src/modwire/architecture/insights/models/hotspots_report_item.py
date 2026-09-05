from modwire.shared.values.models.value_model import ValueModel


class HotspotsReportItem(ValueModel):
    source_id: str
    incoming_count: int
    outgoing_count: int
    pressure_score: int
