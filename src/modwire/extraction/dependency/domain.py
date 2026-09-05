from abc import ABC, abstractmethod

from modwire.shared.code.models.dependency_graph import DependencyGraph
from modwire.shared.code.models.identity import FileId
from modwire.shared.code.models.source_file import SourceFile


class GraphBuilder(ABC):
    @abstractmethod
    def build(self, extracted_files: dict[FileId, SourceFile]) -> DependencyGraph:
        raise NotImplementedError


class ImportResolver(ABC):
    @abstractmethod
    def resolve(self, files: dict[FileId, SourceFile]) -> dict[FileId, SourceFile]:
        raise NotImplementedError
