from collections.abc import Callable, Iterable

from ...values.models.value_model import ValueModel
from .code_map import CodeMap
from .dependency_edge_result import DependencyEdgeResult
from .dependency_node_result import DependencyNodeResult
from .edge import Edge
from .identity import FileId
from .query_builder import QueryBuilder
from .query_types import SourceItem, T
from .source_abstract_class import SourceAbstractClass
from .source_call import SourceCall
from .source_callable import SourceCallable
from .source_class import SourceClass
from .source_export import SourceExport
from .source_file import SourceFile
from .source_file_result import SourceFileResult
from .source_function import SourceFunction
from .source_import import SourceImport
from .source_interface import SourceInterface
from .source_item_result import SourceItemResult
from .source_type import SourceType
from .source_value import SourceValue


class QueryableCodeMap(ValueModel):
    code_map: CodeMap

    @property
    def cm(self) -> CodeMap:
        return self.code_map

    def query(self, items: Iterable[T]) -> QueryBuilder[T]:
        return QueryBuilder(items=tuple(items))

    def source_ids(self) -> tuple[FileId, ...]:
        return tuple(self.code_map.extraction.files)

    def has_source_file(self, source_id: FileId) -> bool:
        return source_id in self.code_map.extraction.files

    def source_file(self, source_id: FileId) -> SourceFileResult | None:
        source_file = self.code_map.extraction.files.get(source_id)
        if source_file is None:
            return None
        return SourceFileResult(source_id=source_id, file=source_file)

    def files(self) -> QueryBuilder[SourceFileResult]:
        return self.source_files()

    def source_files(self) -> QueryBuilder[SourceFileResult]:
        return QueryBuilder(
            items=tuple(
                (
                    SourceFileResult(source_id=source_id, file=source_file)
                    for source_id, source_file in self.code_map.extraction.files.items()
                )
            )
        )

    def imports(self) -> QueryBuilder[SourceItemResult[SourceImport]]:
        return self._source_items(lambda source_file: source_file.imports)

    def exports(self) -> QueryBuilder[SourceItemResult[SourceExport]]:
        return self._source_items(lambda source_file: source_file.exports)

    def classes(self) -> QueryBuilder[SourceItemResult[SourceClass]]:
        return self._source_items(lambda source_file: source_file.classes)

    def interfaces(self) -> QueryBuilder[SourceItemResult[SourceInterface]]:
        return self._source_items(lambda source_file: source_file.interfaces)

    def types(self) -> QueryBuilder[SourceItemResult[SourceType]]:
        return self._source_items(lambda source_file: source_file.types)

    def abstract_classes(self) -> QueryBuilder[SourceItemResult[SourceAbstractClass]]:
        return self._source_items(lambda source_file: source_file.abstract_classes)

    def functions(self) -> QueryBuilder[SourceItemResult[SourceFunction]]:
        return self._source_items(lambda source_file: source_file.functions)

    def values(self) -> QueryBuilder[SourceItemResult[SourceValue]]:
        return self._source_items(lambda source_file: source_file.values)

    def callables(self) -> QueryBuilder[SourceItemResult[SourceCallable]]:
        return self._source_items(lambda source_file: source_file.callables)

    def calls(self) -> QueryBuilder[SourceItemResult[SourceCall]]:
        return self._source_items(lambda source_file: source_file.calls)

    def dependency_nodes(self) -> QueryBuilder[DependencyNodeResult]:
        files = self.code_map.extraction.files
        return QueryBuilder(
            items=tuple(
                (
                    DependencyNodeResult(node_id=node_id, node=node, file=files.get(FileId(node_id)))
                    for node_id, node in self.code_map.dependency_graph.nodes.items()
                )
            )
        )

    def dependency_edges(self) -> QueryBuilder[DependencyEdgeResult]:
        return self._dependency_edges(self.code_map.dependency_graph.edges)

    def outgoing_dependencies(self, source_id: FileId) -> QueryBuilder[DependencyEdgeResult]:
        return self._dependency_edges(self.code_map.dependency_graph.outgoing(source_id))

    def incoming_dependencies(self, source_id: FileId) -> QueryBuilder[DependencyEdgeResult]:
        return self._dependency_edges(self.code_map.dependency_graph.incoming(source_id))

    def dependencies_between(self, source_id: FileId, target_id: FileId) -> QueryBuilder[DependencyEdgeResult]:
        return self._dependency_edges(self.code_map.dependency_graph.edges_between(source_id, target_id))

    def tracked_dependency_edges(self) -> QueryBuilder[DependencyEdgeResult]:
        return self._dependency_edges(self.code_map.dependency_graph.tracked_edges(self.source_ids()))

    def external_dependency_edges(self) -> QueryBuilder[DependencyEdgeResult]:
        return self._dependency_edges(self.code_map.dependency_graph.external_edges(self.source_ids()))

    def _source_items(
        self, selector: Callable[[SourceFile], Iterable[SourceItem]]
    ) -> QueryBuilder[SourceItemResult[SourceItem]]:
        return QueryBuilder(
            items=tuple(
                (
                    SourceItemResult(source_id=source_id, file=source_file, item=item)
                    for source_id, source_file in self.code_map.extraction.files.items()
                    for item in selector(source_file)
                )
            )
        )

    def _dependency_edges(self, edges: Iterable[Edge]) -> QueryBuilder[DependencyEdgeResult]:
        files = self.code_map.extraction.files
        return QueryBuilder(
            items=tuple(
                DependencyEdgeResult(
                    edge=edge,
                    source_file=files.get(edge.from_id),
                    target_file=files.get(edge.to_id) if edge.to_id is not None else None,
                )
                for edge in edges
            )
        )
