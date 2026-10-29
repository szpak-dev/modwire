import hashlib
import json

from modwire.application import (
    CapabilityStatus,
    CodeMap,
    SourceClassMethod,
    SourceDeclaration,
    SourceFile,
)

from .language_capability_matrix.projections.model import ReferenceProjection


class FixtureCodeMapProjector:
    def project(self, code_map: CodeMap, projection: ReferenceProjection, reference: CodeMap) -> CodeMap:
        unsupported_type = next(
            callable_fact.return_type
            for source in reference.extraction.files.values()
            for callable_fact in source.canonical_callables()
            if callable_fact.return_type.kind.value == "unsupported"
        )
        source_ids = {
            item.authored.value.as_posix(): item.canonical.value.as_posix() for item in projection.mappings.sources
        }
        declaration_ids = {item.authored: item.canonical for item in projection.mappings.declarations}
        callable_ids = {item.authored: item.canonical for item in projection.mappings.callables}
        parameter_names = {
            (item.authored_callable, item.authored.value): item.canonical.value
            for item in projection.mappings.parameters
        }

        projected_source_ids: list[str] = []
        projected_source_files: list[SourceFile] = []
        for original_source_id, source_file in code_map.extraction.files.items():
            source_id = source_ids[str(original_source_id)]
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
                        "import_identity": source_id,
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

        runtime = code_map.extraction.manifest.runtime.model_copy(
            update={"version": "fixture 1", "resource_digest": "0" * 64}
        )
        source_artifacts = {artifact.source_id: artifact for artifact in code_map.extraction.manifest.sources}
        artifacts = list(code_map.extraction.manifest.sources)
        artifacts.clear()
        for original_source_id in sorted(code_map.extraction.files):
            source_id = source_ids[str(original_source_id)]
            artifacts.append(
                source_artifacts[str(original_source_id)].model_copy(
                    update={
                        "source_id": source_id,
                        "relative_path": source_id,
                        "content_digest": hashlib.sha256(source_id.encode("utf-8")).hexdigest(),
                    }
                )
            )

        policy = code_map.extraction.manifest.policy
        patterns = ",".join(json.dumps(pattern, ensure_ascii=False) for pattern in policy.excluded_patterns)
        follow_symlinks = "true" if policy.follow_symlinks else "false"
        artifact_documents = [
            '{"content_digest":'
            f"{json.dumps(artifact.content_digest)},"
            f'"relative_path":{json.dumps(artifact.relative_path)},'
            f'"source_id":{json.dumps(artifact.source_id)}}}'
            for artifact in artifacts
        ]
        manifest_document = (
            '{"policy":{"excluded_patterns":['
            f'{patterns}],"follow_symlinks":{follow_symlinks}'
            '},"runtime":{"resource_digest":'
            f'{json.dumps(runtime.resource_digest)},"version":{json.dumps(runtime.version)}'
            f'}},"sources":[{",".join(artifact_documents)}]}}'
        )
        manifest = code_map.extraction.manifest.model_copy(
            update={
                "runtime": runtime,
                "sources": tuple(artifacts),
                "digest": hashlib.sha256(manifest_document.encode("utf-8")).hexdigest(),
            }
        )
        extraction = code_map.extraction.model_copy(
            update={
                "files": files,
                "import_identities": {
                    source_file.import_identity: source_id for source_id, source_file in files.items()
                },
                "manifest": manifest,
                "files_found": len(files),
            }
        )

        extractor = code_map.producer.extractor.model_copy(
            update={
                "id": "fixture.extractor",
                "version": "1",
                "language": "fixture",
                "runtime": "fixture",
            }
        )
        capabilities = tuple(
            coverage.model_copy(
                update={
                    "status": CapabilityStatus.UNSUPPORTED,
                    "explanation": "The common fixture projection does not publish adapter capability claims.",
                }
            )
            for coverage in code_map.producer.capabilities
        )
        relationship_capabilities = tuple(
            coverage.model_copy(
                update={
                    "semantics": CapabilityStatus.UNSUPPORTED,
                    "semantics_explanation": (
                        "The common fixture projection does not publish relationship semantics claims."
                    ),
                    "inventory": CapabilityStatus.UNSUPPORTED,
                    "inventory_explanation": (
                        "The common fixture projection does not publish relationship inventory claims."
                    ),
                }
            )
            for coverage in code_map.producer.relationship_capabilities
        )
        producer = code_map.producer.model_copy(
            update={
                "modwire_version": "fixture",
                "extractor": extractor,
                "capabilities": capabilities,
                "relationship_capabilities": relationship_capabilities,
            }
        )

        nodes = {
            source_ids[str(source_id)]: node.model_copy(update={"id": source_ids[str(source_id)]})
            for source_id, node in code_map.dependency_graph.nodes.items()
        }
        edges = {
            (
                str(edge.from_id),
                str(edge.to_id or ""),
                edge.resolution.value,
                edge.kind.value,
            ): edge
            for edge in code_map.dependency_graph.edges
        }
        edges.clear()
        for edge in code_map.dependency_graph.edges:
            source_id = source_ids[str(edge.from_id)]
            target_id = source_ids[str(edge.to_id)] if edge.to_id is not None else None
            projected_edge = edge.model_copy(
                update={
                    "from_id": source_id,
                    "to_id": target_id,
                    "specifier": target_id if target_id is not None else f"external:{source_id}",
                }
            )
            identity = (
                source_id,
                target_id or "",
                projected_edge.resolution.value,
                projected_edge.kind.value,
            )
            edges[identity] = projected_edge
        dependency_graph = code_map.dependency_graph.model_copy(
            update={
                "nodes": nodes,
                "edges": sorted(
                    edges.values(),
                    key=lambda edge: (
                        str(edge.from_id),
                        str(edge.to_id or ""),
                        edge.resolution.value,
                        edge.kind.value,
                    ),
                ),
            }
        )
        projected = code_map.model_copy(
            update={
                "language": "fixture",
                "producer": producer,
                "extraction": extraction,
                "dependency_graph": dependency_graph,
            }
        )
        return CodeMap.model_validate_json(projected.model_dump_json())
