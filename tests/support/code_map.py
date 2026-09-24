from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

from modwire.application import CodeMap, QueryableCodeMap


class CodeMapFactory:
    def queryable(
        self,
        files: Mapping[str, Mapping[str, object]],
        edges: tuple[tuple[str, str | None, str, str], ...],
    ) -> QueryableCodeMap:
        source_files = {source_id: self.source_file(source_id, values) for source_id, values in files.items()}
        modules = {str(source_file["module_id"]): source_id for source_id, source_file in source_files.items()}
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
                    "kind": "import",
                }
            )
        code_map = CodeMap.model_validate(
            {
                "language": "example",
                "extraction": {
                    "files": source_files,
                    "modules": modules,
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
            "module_id": str(PurePosixPath(source_id).with_suffix("")).replace("/", "."),
            "imports": [],
            "exports": [],
            "classes": [],
            "interfaces": [],
            "types": [],
            "abstract_classes": [],
            "functions": [],
            "values": [],
            "callables": [],
            "calls": [],
            "line_count": 1,
            "code_line_count": 1,
            "public_symbol_count": 0,
        }
        return {**defaults, **values}

    def symbol(self, name: str, *, line_count: int, declared_args: int, optional_args: int) -> dict[str, Any]:
        return {
            "name": name,
            "visibility": "public",
            "visibility_intent": "public",
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
            "visibility": "public",
            "visibility_intent": "public",
            "line_count": line_count,
            "methods": list(methods),
            "properties": list(properties),
        }

    def source_value(self, name: str, *, declaration_kind: str, scope: str) -> dict[str, object]:
        return {
            "name": name,
            "visibility": "public",
            "visibility_intent": "public",
            "line_count": 1,
            "declaration_kind": declaration_kind,
            "value_kind": "literal",
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
            "id": f"{source_id}::{name}",
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

    def source_call(self, source_id: str, source_name: str, target_name: str) -> dict[str, object]:
        return {
            "source_callable_id": f"{source_id}::{source_name}",
            "target_callable_id": f"{source_id}::{target_name}",
            "source_id": source_id,
            "line": 1,
            "expression": target_name,
            "resolution": "resolved",
            "target_name": target_name,
        }
