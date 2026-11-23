from ....shared.values.models.value_model import ValueModel
from .shape_rule_kind import ShapeRuleKind
from .shape_symbol_kind import ShapeSymbolKind


class ShapeViolation(ValueModel):
    source_id: str
    rule_name: ShapeRuleKind
    actual: int | str | bool
    limit: int | str | bool
    realm: str = ""
    symbol_kind: ShapeSymbolKind
    symbol_name: str = ""
