import ast
from abc import ABC, abstractmethod

from ...shared.code.models.identity import ModuleId
from ...shared.code.models.source_file import SourceFile
from .models.batch_config import BatchConfig
from .models.extractor_runtime import ExtractorRuntime
from .models.python_call_context import PythonCallContext


class PythonCallReader(ABC):
    @abstractmethod
    def collect(self, node: ast.AST, context: PythonCallContext) -> list[dict[str, object]]:
        raise NotImplementedError


class SourceParser(ABC):
    @abstractmethod
    def extract(self, content: str, path: str, sources_root: str, source_id: str | None) -> dict[str, object]:
        raise NotImplementedError


class SourceExtractor(ABC):
    @property
    @abstractmethod
    def runtime(self) -> ExtractorRuntime:
        raise NotImplementedError

    @property
    @abstractmethod
    def batch_config(self) -> BatchConfig:
        raise NotImplementedError

    @abstractmethod
    def module_identities(self, source_file: SourceFile) -> tuple[ModuleId, ...]:
        raise NotImplementedError
