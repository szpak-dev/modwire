from modwire.shared.values.models.value_model import ValueModel


class ReportMetadata(ValueModel):
    id: str
    title: str
    description: str
    model: str
    path: str
    order: int
    children: tuple["ReportMetadata", ...] = ()
