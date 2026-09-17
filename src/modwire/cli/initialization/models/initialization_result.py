from pathlib import Path

from ....shared.values.models.value_model import ValueModel


class InitializationResult(ValueModel):
    created: tuple[Path, ...] = ()
    preserved: tuple[Path, ...] = ()
    overwritten: tuple[Path, ...] = ()
