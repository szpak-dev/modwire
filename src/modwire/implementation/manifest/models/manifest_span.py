from ....shared.values.models.value_model import ValueModel


class ManifestSpan(ValueModel):
    target_id: str
    line_start: int
    line_end: int
