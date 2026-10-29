import hashlib
import json
import re
from pathlib import PurePosixPath

from modwire.application import (
    CapabilityStatus,
    CodeMap,
    DeclarationIdentity,
    SourceCallableKind,
    SourceClassMethod,
    SourceTypeUnsupported,
)


class FixtureCodeMapProjector:
    def canonical_name(self, name: str) -> str:
        separated = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name.replace("-", "_"))
        return re.sub("([A-Z]+)([A-Z][a-z])", r"\1_\2", separated).lower()

    def project_method(
        self,
        method: SourceClassMethod,
        source_id: str,
        owner_declaration_id: DeclarationIdentity,
        ordinal: int,
    ) -> SourceClassMethod:
        name = self.canonical_name(method.name)
        qualified_name = f"{owner_declaration_id.qualified_name}.{name}"
        return method.model_copy(
            update={
                "name": name,
                "source_id": source_id,
                "qualified_name": qualified_name,
                "declaration_id": method.declaration_id.model_copy(
                    update={
                        "source_id": source_id,
                        "qualified_name": qualified_name,
                        "ordinal": ordinal,
                    }
                ),
                "owner_declaration_id": owner_declaration_id,
                "parameters": tuple(
                    parameter.model_copy(
                        update={
                            "name": self.canonical_name(parameter.name),
                            "type": SourceTypeUnsupported(),
                        }
                    )
                    for parameter in method.parameters
                ),
                "return_type": SourceTypeUnsupported(),
                "decorators": (),
                "docstring": "",
                "declaration_annotations": (),
                "line_count": 0,
                "line_start": 0,
                "line_end": 0,
            }
        )

    def project(self, code_map: CodeMap) -> CodeMap:
        source_ids: dict[str, str] = {}
        for source_id in code_map.extraction.files:
            path = PurePosixPath(str(source_id))
            canonical_name = self.canonical_name(path.stem)
            source_ids[str(source_id)] = str(PurePosixPath(*path.parts[:-1], canonical_name))

        projected_source_ids: list[str] = []
        projected_source_files = list(code_map.extraction.files.values())
        projected_source_files.clear()
        for original_source_id, source_file in code_map.extraction.files.items():
            source_id = source_ids[str(original_source_id)]
            projected_source_ids.append(source_id)
            declarations = list(source_file.declarations)
            declarations.clear()
            for ordinal, declaration in enumerate(sorted(source_file.declarations, key=lambda item: item.name), 1):
                identity = declaration.declaration_id.model_copy(
                    update={
                        "source_id": source_id,
                        "qualified_name": declaration.name,
                        "ordinal": ordinal,
                    }
                )
                methods = tuple(
                    self.project_method(method, source_id, identity, method_ordinal)
                    for method_ordinal, method in enumerate(
                        (
                            method
                            for method in sorted(declaration.methods, key=lambda item: item.name)
                            if method.kind is not SourceCallableKind.CONSTRUCTOR
                        ),
                        start=1,
                    )
                )
                abstract_methods = tuple(
                    self.project_method(method, source_id, identity, method_ordinal)
                    for method_ordinal, method in enumerate(
                        (
                            method
                            for method in sorted(declaration.abstract_methods, key=lambda item: item.name)
                            if method.kind is not SourceCallableKind.CONSTRUCTOR
                        ),
                        start=1,
                    )
                )
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
