from collections.abc import Callable, Iterable

from ....values.models.value_model import ValueModel
from ..callables.source_call import SourceCall
from ..callables.source_callable import SourceCallable
from ..callables.source_callable_value import SourceCallableValue
from ..callables.source_function import SourceFunction
from ..declarations.declaration_family import DeclarationFamily
from ..declarations.source_declaration import SourceDeclaration
from ..declarations.source_declaration_relation import SourceDeclarationRelation
from ..declarations.source_namespace import SourceNamespace
from ..dependencies.edge import Edge
from ..maps.code_map import CodeMap
from ..sources.identity import FileId
from ..sources.source_export import SourceExport
from ..sources.source_file import SourceFile
from ..sources.source_import import SourceImport
from ..values.source_value import SourceValue
from .dependency_edge_result import DependencyEdgeResult
from .dependency_node_result import DependencyNodeResult
from .query_builder import QueryBuilder
from .query_types import SourceItem, T
from .source_file_result import SourceFileResult
from .source_item_result import SourceItemResult


class QueryableCodeMap(ValueModel):
    code_map: CodeMap

    @property
    def cm(self) -> CodeMap:
        return self.code_map

    def query(self, items: Iterable[T]) -> QueryBuilder[T]:
        return QueryBuilder[T].model_construct(items=tuple(items), predicates=())

    def source_ids(self) -> tuple[FileId, ...]:
        return tuple(self.code_map.extraction.files)

    def has_source_file(self, source_id: FileId) -> bool:
        return source_id in self.code_map.extraction.files

    def source_file(self, source_id: FileId) -> SourceFileResult | None:
        source_file = self.code_map.extraction.files.get(source_id)
        if source_file is None:
            return None
        return SourceFileResult.model_construct(source_id=source_id, file=source_file)

    def files(self) -> QueryBuilder[SourceFileResult]:
        return self.source_files()

    def source_files(self) -> QueryBuilder[SourceFileResult]:
        return QueryBuilder[SourceFileResult].model_construct(
            items=tuple(
                SourceFileResult.model_construct(source_id=source_id, file=source_file)
                for source_id, source_file in self.code_map.extraction.files.items()
            ),
            predicates=(),
        )

    def imports(self) -> QueryBuilder[SourceItemResult[SourceImport]]:
        return self.source_items(lambda source_file: source_file.imports)

    def exports(self) -> QueryBuilder[SourceItemResult[SourceExport]]:
        return self.source_items(lambda source_file: source_file.exports)

    def namespaces(self) -> QueryBuilder[SourceItemResult[SourceNamespace]]:
        return self.source_items(lambda source_file: source_file.namespaces)

    def declarations(self) -> QueryBuilder[SourceItemResult[SourceDeclaration]]:
        return self.source_items(lambda source_file: source_file.declarations)

    def classes(self) -> QueryBuilder[SourceItemResult[SourceDeclaration]]:
        return self.declarations_in_family(DeclarationFamily.CLASS)

    def interfaces(self) -> QueryBuilder[SourceItemResult[SourceDeclaration]]:
        return self.declarations_in_family(DeclarationFamily.INTERFACE)

    def types(self) -> QueryBuilder[SourceItemResult[SourceDeclaration]]:
        return self.declarations_in_family(DeclarationFamily.TYPE)

    def abstract_classes(self) -> QueryBuilder[SourceItemResult[SourceDeclaration]]:
        return self.declarations_in_family(DeclarationFamily.ABSTRACT_CLASS)

    def functions(self) -> QueryBuilder[SourceItemResult[SourceFunction]]:
        return self.source_items(lambda source_file: source_file.functions)

    def values(self) -> QueryBuilder[SourceItemResult[SourceValue | SourceCallableValue]]:
        return self.source_items(
            lambda source_file: (*source_file.values, *source_file.callable_values)
        )

    def callables(self) -> QueryBuilder[SourceItemResult[SourceCallable]]:
        return self.source_items(lambda source_file: source_file.canonical_callables())

    def calls(self) -> QueryBuilder[SourceItemResult[SourceCall]]:
        return self.source_items(lambda source_file: source_file.calls)

    def declaration_relations(self) -> QueryBuilder[SourceItemResult[SourceDeclarationRelation]]:
        return self.source_items(lambda source_file: source_file.declaration_relations)

    def dependency_nodes(self) -> QueryBuilder[DependencyNodeResult]:
        files = self.code_map.extraction.files
        return QueryBuilder[DependencyNodeResult].model_construct(
            items=tuple(
                DependencyNodeResult.model_construct(node_id=node_id, node=node, file=files.get(FileId(node_id)))
                for node_id, node in self.code_map.dependency_graph.nodes.items()
            ),
            predicates=(),
        )

    def dependency_edges(self) -> QueryBuilder[DependencyEdgeResult]:
        return self.dependency_edges_for(self.code_map.dependency_graph.edges)

    def outgoing_dependencies(self, source_id: FileId) -> QueryBuilder[DependencyEdgeResult]:
        return self.dependency_edges_for(self.code_map.dependency_graph.outgoing(source_id))

    def incoming_dependencies(self, source_id: FileId) -> QueryBuilder[DependencyEdgeResult]:
        return self.dependency_edges_for(self.code_map.dependency_graph.incoming(source_id))

    def dependencies_between(self, source_id: FileId, target_id: FileId) -> QueryBuilder[DependencyEdgeResult]:
        return self.dependency_edges_for(self.code_map.dependency_graph.edges_between(source_id, target_id))

    def tracked_dependency_edges(self) -> QueryBuilder[DependencyEdgeResult]:
        return self.dependency_edges_for(self.code_map.dependency_graph.tracked_edges(self.source_ids()))

    def external_dependency_edges(self) -> QueryBuilder[DependencyEdgeResult]:
        return self.dependency_edges_for(self.code_map.dependency_graph.external_edges(self.source_ids()))

    def declarations_in_family(self, family: DeclarationFamily) -> QueryBuilder[SourceItemResult[SourceDeclaration]]:
        return self.source_items(
            lambda source_file: (
                item for item in source_file.declarations if source_file.declaration_family(item.kind) is family
            )
        )

    def source_items(
        self, selector: Callable[[SourceFile], Iterable[SourceItem]]
    ) -> QueryBuilder[SourceItemResult[SourceItem]]:
        return QueryBuilder[SourceItemResult[SourceItem]].model_construct(
            items=tuple(
                SourceItemResult[SourceItem].model_construct(source_id=source_id, file=source_file, item=item)
                for source_id, source_file in self.code_map.extraction.files.items()
                for item in selector(source_file)
            ),
            predicates=(),
        )

    def dependency_edges_for(self, edges: Iterable[Edge]) -> QueryBuilder[DependencyEdgeResult]:
        files = self.code_map.extraction.files
        return QueryBuilder[DependencyEdgeResult].model_construct(
            items=tuple(
                DependencyEdgeResult.model_construct(
                    edge=edge,
                    source_file=files.get(edge.from_id),
                    target_file=files.get(edge.to_id) if edge.to_id is not None else None,
                )
                for edge in edges
            ),
            predicates=(),
        )
