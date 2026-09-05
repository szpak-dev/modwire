from dataclasses import dataclass
from pathlib import Path

from pydantic_yaml import parse_yaml_file_as
from wireup import injectable

from modwire.architecture.config.models.architecture_config import ArchitectureConfig


@injectable
@dataclass(frozen=True)
class ConfigurationLoader:
    def load(self, dot_dir: Path) -> ArchitectureConfig:
        return parse_yaml_file_as(ArchitectureConfig, dot_dir / "architecture.yaml")
