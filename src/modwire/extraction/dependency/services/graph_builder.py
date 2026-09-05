from dataclasses import dataclass

from wireup import injectable

from modwire.shared.code.models.dependency_graph import DependencyGraph
from modwire.shared.code.models.identity import FileId
from modwire.shared.code.models.source_file import SourceFile

from ..domain import GraphBuilder


@injectable(as_type=GraphBuilder)
@dataclass(frozen=True)
class DependencyGraphBuilder(GraphBuilder):
    def build(self, extracted_files: dict[FileId, SourceFile]) -> DependencyGraph:
        graph = DependencyGraph()
        for file_path, extracted_file in extracted_files.items():
            graph.add_node(file_path)
            for imported_reference in extracted_file.imports:
                graph.add_edge(
                    file_path,
                    imported_reference.target_file_id,
                    specifier=imported_reference.normalized_path,
                    resolution=imported_reference.resolution,
                )
        return graph
