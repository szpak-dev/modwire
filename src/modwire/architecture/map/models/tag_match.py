from ....shared.values.models.value_model import ValueModel


class TagMatch(ValueModel):
    name: str
    pattern: str
    matched_path: str
    captured_path: str
    is_wildcard: bool
    wildcard_values: tuple[str, ...] = ()
