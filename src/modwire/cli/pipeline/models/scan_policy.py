from ....shared.values.models.value_model import ValueModel


class ScanPolicy(ValueModel):
    excluded_patterns: tuple[str, ...] = ()
    follow_symlinks: bool = False
