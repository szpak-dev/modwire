from ....shared.values.models.value_model import ValueModel


class ExtractorResource(ValueModel):
    package: str
    path: str
