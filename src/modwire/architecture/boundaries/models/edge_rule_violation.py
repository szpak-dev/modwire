from ....shared.values.models.value_model import ValueModel


class EdgeRuleViolation(ValueModel):
    source_id: str
    target_id: str
    source_pattern: str
    target_pattern: str
    rule_name: str
