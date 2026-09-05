from ...values.models.value_model import ValueModel


class SourceClassProperty(ValueModel):
    name: str
    is_optional: bool
