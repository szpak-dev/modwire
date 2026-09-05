from ....shared.values.models.value_model import ValueModel


class ClustersReportItem(ValueModel):
    name: str
    files: tuple[str, ...]
    incoming_count: int
    outgoing_count: int
    pressure_score: int
    top_files: tuple[str, ...]
