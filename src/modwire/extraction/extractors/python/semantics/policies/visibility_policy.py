from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_visibility import SourceVisibility


class PythonVisibilityPolicy(ABC):
    @abstractmethod
    def classify(self, name: str) -> SourceVisibility:
        raise NotImplementedError


@injectable(as_type=PythonVisibilityPolicy)
@dataclass(frozen=True)
class NameVisibilityPolicy(PythonVisibilityPolicy):
    def classify(self, name: str) -> SourceVisibility:
        is_language_name = name.startswith("__") and name.endswith("__")
        if name.startswith("__") and not is_language_name:
            return SourceVisibility.PRIVATE
        if name.startswith("_") and not is_language_name:
            return SourceVisibility.PROTECTED
        return SourceVisibility.PUBLIC
