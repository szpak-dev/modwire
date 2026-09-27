from ....shared.values.models.value_model import ValueModel


class ManifestAnnotation(ValueModel):
    target_id: str
    role: str
    expression: str
