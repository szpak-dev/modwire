from pathlib import Path

from ....shared.values.models.value_model import ValueModel
from .command_name import CommandName


class CommandRequest(ValueModel):
    command: CommandName
    dot_dir: Path
    architecture_root: Path = Path(".")
    language: str = ""
    summary: bool = False
    force: bool = False
    cache_directory: Path = Path(".modwire/cache")
    cache_namespace: str = "default"
    cache_max_bytes: int = 512 * 1024 * 1024
    no_cache: bool = False
