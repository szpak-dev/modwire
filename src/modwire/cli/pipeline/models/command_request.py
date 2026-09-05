from pathlib import Path
from typing import Literal

from modwire.shared.values.models.value_model import ValueModel


class CommandRequest(ValueModel):
    command: Literal["init", "report"]
    dot_dir: Path
    architecture_root: Path = Path(".")
    language: str = ""
    summary: bool = False
    force: bool = False
