from abc import ABC, abstractmethod
from pathlib import Path

from .....shared.values.models.value_model import ValueModel


class ExtractorEntrypoint(ValueModel, ABC):
    package: str
    path: str

    @abstractmethod
    def command_arguments(self, resource_path: Path) -> tuple[str, ...]: ...
