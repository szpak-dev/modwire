import hashlib
import json
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

from modwire.application import CodeMap, FactCapability, QueryableCodeMap, RelationshipFamily


class CodeMapFactory:
    def queryable(
        self,
        files: Mapping[str, Mapping[str, object]],
        edges: tuple[tuple[str, str | None, str, str], ...],
    ) -> QueryableCodeMap:
        source_files = {source_id: self.source_file(source_id, values) for source_id, values in files.items()}
        import_identities = {
            str(source_file["import_identity"]): source_id for source_id, source_file in source_files.items()
        }
        nodes = {source_id: {"id": source_id, "kind": "file"} for source_id in source_files}
        dependency_edges = []
        for source_id, target_id, resolution, specifier in edges:
            if target_id is not None:
                nodes.setdefault(target_id, {"id": target_id, "kind": "file"})
            dependency_edges.append(
                {
                    "from_id": source_id,
                    "to_id": target_id,
                    "specifier": specifier,
                    "resolution": resolution,
                    "kind": "imports",
                }
            )
        source_artifacts = [
            {
                "source_id": source_id,
                "relative_path": source_id,
                "content_digest": hashlib.sha256(source_id.encode("utf-8")).hexdigest(),
            }
            for source_id in sorted(source_files)
        ]
        source_manifest_payload = {
            "policy": {"excluded_patterns": [], "follow_symlinks": False},
            "runtime": {"version": "example 1", "resource_digest": "0" * 64},
            "sources": source_artifacts,
        }
        source_manifest_digest = hashlib.sha256(
            json.dumps(
                source_manifest_payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        code_map = CodeMap.model_validate(
            {
                "language": "example",
                "producer": {
                    "modwire_version": "1.0.0",
                    "extractor": {
                        "id": "example.extractor",
                        "version": "1",
                        "language": "example",
                        "runtime": "example",
                    },
                    "capabilities": [
                        {
                            "capability": capability.value,
                            "status": "unsupported",
                            "explanation": "Synthetic test maps do not claim extractor coverage.",
                        }
                        for capability in FactCapability
                    ],
                    "relationship_capabilities": [
                        {
                            "family": family.value,
                            "evidence_requirements": [capability.value for capability in family.evidence_requirements],
                            "semantics": "unsupported",
                            "semantics_explanation": "Synthetic test maps do not claim relationship semantics.",
                            "inventory": "unsupported",
                            "inventory_explanation": "Synthetic test maps do not claim relationship inventory.",
                        }
                        for family in RelationshipFamily
                    ],
                },
                "extraction": {
                    "files": source_files,
                    "import_identities": import_identities,
                    "manifest": {
                        **source_manifest_payload,
                        "digest_algorithm": "sha256",
                        "digest": source_manifest_digest,
                    },
                    "files_found": len(source_files),
                    "files_excluded": 0,
                    "directories_pruned": 0,
                },
                "dependency_graph": {"nodes": nodes, "edges": dependency_edges},
            }
        )
        return QueryableCodeMap(code_map=code_map)

    def source_file(self, source_id: str, values: Mapping[str, object]) -> dict[str, object]:
        defaults: dict[str, object] = {
            "file_id": source_id,
            "import_identity": str(PurePosixPath(source_id).with_suffix("")),
            "imports": [],
            "exports": [],
            "namespaces": [],
            "declarations": [],
            "functions": [],
            "values": [],
            "callables": [],
            "calls": [],
            "declaration_relations": [],
            "line_count": 1,
            "code_line_count": 1,
            "public_symbol_count": 0,
        }
        source_file = {**defaults, **values}
        declaration_families = {
            "class": "class",
            "record": "class",
            "enum": "class",
            "abstract_class": "abstract_class",
            "interface": "interface",
            "annotation": "interface",
            "trait": "type",
            "module": "type",
            "type_alias": "type",
        }
        for collection, family in (("functions", "function"), ("values", "value")):
            source_file[collection] = [
                {
                    **declaration,
                    "declaration_id": {
                        "source_id": source_id,
                        "family": family,
                        "qualified_name": declaration["name"],
                        "ordinal": ordinal,
                    },
                }
                for ordinal, declaration in enumerate(source_file[collection], start=1)
            ]
        source_file["declarations"] = [
            {
                **declaration,
                "declaration_id": {
                    "source_id": source_id,
                    "family": declaration_families[str(declaration["kind"])],
                    "qualified_name": declaration["name"],
                    "ordinal": ordinal,
                },
            }
            for ordinal, declaration in enumerate(source_file["declarations"], start=1)
        ]
        source_file["callables"] = [
            {
                **callable_definition,
                "declaration_id": {
                    "source_id": source_id,
                    "family": "function",
                    "qualified_name": callable_definition["qualified_name"],
                    "ordinal": ordinal,
                },
            }
            for ordinal, callable_definition in enumerate(source_file["callables"], start=1)
        ]
        callable_ids = {
            callable_definition["qualified_name"]: callable_definition["declaration_id"]
            for callable_definition in source_file["callables"]
        }
        source_file["calls"] = [
            {
                **call,
                "source_callable_id": callable_ids[call["source_callable_id"]],
                "target_callable_id": callable_ids[call["target_callable_id"]],
            }
            for call in source_file["calls"]
        ]
        return source_file

    def symbol(self, name: str, *, line_count: int, declared_args: int, optional_args: int) -> dict[str, Any]:
        return {
            "name": name,
            "visibility": "public",
            "visibility_intent": "public",
            "declaration_annotations": [],
            "line_count": line_count,
            "declared_args": declared_args,
            "optional_args": optional_args,
        }

    def source_class(
        self,
        name: str,
        *,
        line_count: int,
        methods: tuple[Mapping[str, object], ...],
        properties: tuple[Mapping[str, object], ...],
    ) -> dict[str, object]:
        return {
            "name": name,
            "kind": "class",
            "visibility": "public",
            "visibility_intent": "public",
            "declaration_annotations": [],
            "line_count": line_count,
            "methods": list(methods),
            "properties": [
                {
                    "annotation": "",
                    "visibility": "public",
                    "member_kind": "instance",
                    "assigned_values": [{"kind": "unassigned", "expression": "", "reference": ""}],
                    **property_definition,
                }
                for property_definition in properties
            ],
        }

    def source_value(self, name: str, *, declaration_kind: str, scope: str) -> dict[str, object]:
        return {
            "name": name,
            "visibility": "public",
            "visibility_intent": "public",
            "line_count": 1,
            "declaration_kind": declaration_kind,
            "value_kind": "value_literal",
            "scope": scope,
            "declared_args": 0,
            "optional_args": 0,
        }

    def source_import(
        self,
        specifier: str,
        *,
        imported_name: str,
        is_aliased: bool,
        imported_symbols: tuple[Mapping[str, object], ...],
    ) -> dict[str, object]:
        return {
            "path": specifier,
            "is_relative": False,
            "normalized_path": specifier,
            "imported_name": imported_name,
            "is_aliased": is_aliased,
            "crossing_type": "module",
            "file_barrier_crossed": False,
            "statement_id": 1,
            "join_key": specifier,
            "uses_joined_import": True,
            "resolution": "external",
            "target_file_id": None,
            "imported_symbols": list(imported_symbols),
        }

    def source_export(self, name: str) -> dict[str, object]:
        return {
            "name": name,
            "local_name": name,
            "kind": "value",
            "crossing_type": "symbol",
            "path": "",
            "is_relative": False,
            "normalized_path": "",
            "is_reexport": False,
            "is_default": False,
            "is_aliased": False,
            "statement_id": 0,
        }

    def source_callable(self, source_id: str, name: str) -> dict[str, object]:
        return {
            **self.symbol(name, line_count=1, declared_args=0, optional_args=0),
            "source_id": source_id,
            "qualified_name": name,
            "owner_name": "",
            "kind": "function",
            "line_start": 1,
            "line_end": 1,
            "parameters": [],
            "return_annotation": "",
            "decorators": [],
            "docstring": "",
        }

    def source_call(
        self,
        source_id: str,
        source_name: str,
        target_name: str,
        *,
        ordinal: int,
    ) -> dict[str, object]:
        return {
            "source_callable_id": source_name,
            "ordinal": ordinal,
            "target_callable_id": target_name,
            "source_id": source_id,
            "line": 1,
            "expression": target_name,
            "resolution": "resolved",
            "target_name": target_name,
        }
