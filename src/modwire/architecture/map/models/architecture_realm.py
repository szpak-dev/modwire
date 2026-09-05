from ....shared.values.models.value_model import ValueModel


class ArchitectureRealm(ValueModel):
    name: str
    module_tag: str
    layers: tuple[str, ...] = ()
