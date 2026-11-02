from modwire.application import (
    CodeMap,
    DependencyGraph,
    Edge,
    FileId,
    ImportIdentity,
    ImportSpecifier,
    SourceClassMethod,
    SourceDeclaration,
    SourceDependencyKind,
    SourceDependencyResolution,
    SourceFile,
    SourceTypeUnsupported,
)

from .fixture_contract_error import FixtureContractError
from .language_capability_matrix.oracle.ownership import FixtureSourceOwnership
from .language_capability_matrix.projections.reference_projection import ReferenceProjection


class FixtureCodeMapProjector:
    def project(self, code_map: CodeMap, projection: ReferenceProjection, reference: CodeMap) -> CodeMap:
        if not FixtureSourceOwnership(frozenset(code_map.extraction.files)).accepts(
            code_map.dependency_graph, code_map.extraction.manifest
        ):
            raise FixtureContractError("reference projection requires consistent source paths and graph identities")
        unsupported_type = SourceTypeUnsupported()
        source_ids = {
            FileId(item.authored.value.as_posix()): FileId(item.canonical.value.as_posix())
            for item in projection.mappings.sources
        }
        if set(code_map.extraction.files) != set(source_ids):
            raise FixtureContractError("reference projection source inventory differs from its declared aliases")
        if code_map.extraction.manifest.policy != reference.extraction.manifest.policy:
            raise FixtureContractError("reference projection scan policy differs from its canonical scenario")
        declaration_ids = {item.authored: item.canonical for item in projection.mappings.declarations}
        callable_ids = {item.authored: item.canonical for item in projection.mappings.callables}
        parameter_names = {
            (item.authored_callable, item.authored.value): item.canonical.value
            for item in projection.mappings.parameters
        }

        projected_source_ids: list[FileId] = []
        projected_source_files: list[SourceFile] = []
        for original_source_id, source_file in code_map.extraction.files.items():
            source_id = source_ids[original_source_id]
            projected_source_ids.append(source_id)
            declarations: list[SourceDeclaration] = []
            for declaration in sorted(source_file.declarations, key=lambda item: item.name):
                identity = declaration_ids[declaration.declaration_id]
                projected_method_groups: list[tuple[SourceClassMethod, ...]] = []
                for authored_methods in (declaration.methods, declaration.abstract_methods):
                    projected_methods: list[SourceClassMethod] = []
                    for method in sorted(authored_methods, key=lambda item: item.name):
                        if method.declaration_id not in callable_ids:
                            continue
                        callable_identity = callable_ids[method.declaration_id]
                        name = callable_identity.qualified_name.rsplit(".", 1)[-1]
                        projected_methods.append(
                            method.model_copy(
                                update={
                                    "name": name,
                                    "source_id": source_id,
                                    "qualified_name": callable_identity.qualified_name,
                                    "declaration_id": callable_identity,
                                    "owner_declaration_id": identity,
                                    "parameters": tuple(
                                        parameter.model_copy(
                                            update={
                                                "name": parameter_names[(method.declaration_id, parameter.name)],
                                                "type": unsupported_type,
                                            }
                                        )
                                        for parameter in method.parameters
                                    ),
                                    "return_type": unsupported_type,
                                    "decorators": (),
                                    "docstring": "",
                                    "declaration_annotations": (),
                                    "line_count": 0,
                                    "line_start": 0,
                                    "line_end": 0,
                                }
                            )
                        )
                    projected_method_groups.append(tuple(projected_methods))
                methods, abstract_methods = projected_method_groups
                declarations.append(
                    declaration.model_copy(
                        update={
                            "name": identity.qualified_name,
                            "declaration_id": identity,
                            "declaration_annotations": (),
                            "line_count": 0,
                            "methods": methods,
                            "abstract_methods": abstract_methods,
                            "properties": (),
                            "signatures": (),
                        }
                    )
                )
            projected_source_files.append(
                source_file.model_copy(
                    update={
                        "file_id": source_id,
                        "import_identity": ImportIdentity(source_id),
                        "imports": [],
                        "exports": [],
                        "namespaces": (),
                        "declarations": tuple(declarations),
                        "functions": (),
                        "values": (),
                        "callable_values": (),
                        "anonymous_callables": (),
                        "calls": (),
                        "declaration_relations": (),
                        "line_count": 0,
                        "code_line_count": 0,
                        "public_symbol_count": sum(
                            declaration.visibility is declaration.visibility.PUBLIC for declaration in declarations
                        ),
                    }
                )
            )
        files = dict(zip(projected_source_ids, projected_source_files, strict=True))

        extraction = code_map.extraction.model_copy(
            update={
                "files": files,
                "import_identities": {
                    source_file.import_identity: source_id for source_id, source_file in files.items()
                },
                "manifest": reference.extraction.manifest,
            }
        )

        nodes = {
            source_ids[source_id]: node.model_copy(update={"id": source_ids[node.id]})
            for source_id, node in code_map.dependency_graph.nodes.items()
        }
        edges: dict[tuple[FileId, FileId | None, SourceDependencyResolution, SourceDependencyKind], Edge] = {}
        for edge in code_map.dependency_graph.edges:
            source_id = source_ids[edge.from_id]
            target_id = source_ids[edge.to_id] if edge.to_id is not None else None
            projected_edge = edge.model_copy(
                update={
                    "from_id": source_id,
                    "to_id": target_id,
                    "specifier": ImportSpecifier(target_id if target_id is not None else f"external:{source_id}"),
                }
            )
            identity = (
                source_id,
                target_id,
                projected_edge.resolution,
                projected_edge.kind,
            )
            edges[identity] = projected_edge
        dependency_graph = DependencyGraph(
            nodes=nodes,
            edges=sorted(
                edges.values(),
                key=lambda edge: (
                    str(edge.from_id),
                    str(edge.to_id or ""),
                    edge.resolution.value,
                    edge.kind.value,
                ),
            ),
        )
        return code_map.model_copy(
            update={
                "language": reference.language,
                "producer": reference.producer,
                "extraction": extraction,
                "dependency_graph": dependency_graph,
            }
        )
