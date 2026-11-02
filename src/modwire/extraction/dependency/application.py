from dataclasses import dataclass

from wireup import injectable

from ...shared.code.models.dependencies.dependency_graph import DependencyGraph
from ...shared.code.models.sources.identity import FileId, ImportIdentity
from ...shared.code.models.sources.source_file import SourceFile
from .domain import GraphBuilder, ImportResolver


@injectable
@dataclass(frozen=True)
class DependencyApplication:
    builder: GraphBuilder
    resolver: ImportResolver

    def build(self, files: dict[FileId, SourceFile]) -> DependencyGraph:
        return self.builder.build(files)

    def resolve(
        self, files: dict[FileId, SourceFile], identities: dict[FileId, tuple[ImportIdentity, ...]]
    ) -> dict[FileId, SourceFile]:
        return self.resolver.resolve(files, identities)
