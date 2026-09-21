from pathlib import Path
from typing import Literal

from ....shared.values.models.value_model import ValueModel


class CommandRequest(ValueModel):
    command: Literal["init", "report", "cache-clear"]
    dot_dir: Path
    architecture_root: Path = Path(".")
    language: str = ""
    summary: bool = False
    force: bool = False
    cache_directory: Path = Path(".modwire/cache")
    cache_namespace: str = "default"
    cache_max_bytes: int = 512 * 1024 * 1024
    no_cache: bool = False
