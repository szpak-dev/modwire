from modwire.shared.values.models.value_model import ValueModel


class PythonBatchInput(ValueModel):
    paths: dict[str, str]
