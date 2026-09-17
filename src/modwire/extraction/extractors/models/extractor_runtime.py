from ....shared.values.models.value_model import ValueModel


class ExtractorRuntime(ValueModel):
    order: int
    language: str
    file_extensions: tuple[str, ...]
    command: tuple[str, ...]
    resource: str
