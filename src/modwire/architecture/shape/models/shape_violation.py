from modwire.shared.values.models.value_model import ValueModel


class ShapeViolation(ValueModel):
    source_id: str
    rule_name: str
    actual: int | str | bool
    limit: int | str | bool
    realm: str = ""
    symbol_kind: str = ""
    symbol_name: str = ""
