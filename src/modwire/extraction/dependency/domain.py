from abc import ABC, abstractmethod

from ...shared.code.models.dependencies.dependency_graph import DependencyGraph
from ...shared.code.models.sources.identity import FileId, ImportIdentity
from ...shared.code.models.sources.source_file import SourceFile


class GraphBuilder(ABC):
    @abstractmethod
    def build(self, extracted_files: dict[FileId, SourceFile]) -> DependencyGraph:
        raise NotImplementedError


class ImportResolver(ABC):
    @abstractmethod
    def resolve(
        self, files: dict[FileId, SourceFile], identities: dict[FileId, tuple[ImportIdentity, ...]]
    ) -> dict[FileId, SourceFile]:
        raise NotImplementedError
