from ....shared.values.models.value_model import ValueModel


class FlowViolation(ValueModel):
    violation_type: str
    path: tuple[str, ...]
    violation_index: int
    rule_name: str
    message: str
    source_module: str = ""
    target_module: str = ""

    def violation_key(self) -> tuple[object, ...]:
        return (
            self.violation_type,
            self.path,
            self.violation_index,
            self.rule_name,
            self.message,
            self.source_module,
            self.target_module,
        )
