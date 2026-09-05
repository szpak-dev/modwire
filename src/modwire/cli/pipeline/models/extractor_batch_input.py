from ....shared.values.models.value_model import ValueModel


class ExtractorBatchInput(ValueModel):
    paths: dict[str, str]
