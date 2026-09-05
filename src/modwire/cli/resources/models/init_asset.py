from pathlib import Path
from typing import Literal

from modwire.shared.values.models.value_model import ValueModel


class InitAsset(ValueModel):
    """Describe one packaged initialization file and its project destination."""

    source: str
    target_base: Literal["project", "dot_dir"]
    target: Path
