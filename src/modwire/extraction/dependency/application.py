from dataclasses import dataclass

from wireup import injectable

from modwire.shared.code.models.dependency_graph import DependencyGraph
from modwire.shared.code.models.identity import FileId
from modwire.shared.code.models.source_file import SourceFile

from .domain import GraphBuilder, ImportResolver


@injectable
@dataclass(frozen=True)
class DependencyApplication:
    builder: GraphBuilder
    resolver: ImportResolver

    def build(self, files: dict[FileId, SourceFile]) -> DependencyGraph:
        return self.builder.build(files)

    def resolve(self, files: dict[FileId, SourceFile]) -> dict[FileId, SourceFile]:
        return self.resolver.resolve(files)
