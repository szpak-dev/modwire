from dataclasses import dataclass
from pathlib import Path

from pydantic_yaml import parse_yaml_file_as

from .matrix import LanguageCapabilityMatrix


@dataclass(frozen=True)
class LanguageCapabilityMatrixReader:
    def read(self, path: Path) -> LanguageCapabilityMatrix:
        return parse_yaml_file_as(LanguageCapabilityMatrix, path)
