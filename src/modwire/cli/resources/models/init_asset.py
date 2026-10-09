from pathlib import Path

from ....shared.values.models.value_model import ValueModel
from .init_target_base import InitTargetBase


class InitAsset(ValueModel):
    source: str
    target_base: InitTargetBase
    target: Path
