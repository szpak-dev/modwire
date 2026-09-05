from modwire.shared.values.models.value_model import ValueModel


class SourceImportedSymbol(ValueModel):
    name: str
    alias: str
    is_aliased: bool
    is_default: bool
    is_namespace: bool
    is_star: bool
