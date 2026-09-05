from ....shared.values.models.value_model import ValueModel


class ArchitectureGroup(ValueModel):
    name: str
    source_ids: tuple[str, ...]
