from pathlib import Path

from ....shared.values.models.value_model import ValueModel


class InitializationResult(ValueModel):
    """Record which initialization assets were created, preserved, or overwritten."""

    created: tuple[Path, ...] = ()
    preserved: tuple[Path, ...] = ()
    overwritten: tuple[Path, ...] = ()
