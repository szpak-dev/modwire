from ....shared.values.models.value_model import ValueModel


class ScanPolicy(ValueModel):
    """Caller-owned filesystem traversal policy with explicit exclusions and opt-in symlink following."""

    excluded_patterns: tuple[str, ...] = ()
    follow_symlinks: bool = False
