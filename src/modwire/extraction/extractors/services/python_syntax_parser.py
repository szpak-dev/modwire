import ast
from dataclasses import dataclass
from typing import cast

from wireup import injectable

from ..domain import PythonCallReader, SourceParser
from ..models.python_call_context import PythonCallContext


@injectable(as_type=SourceParser, qualifier="python")
@dataclass(frozen=True)
class PythonSyntaxParser(SourceParser):
    calls: PythonCallReader

    def line_span(self, node: ast.stmt | ast.expr) -> int:
        return cast(int, node.end_lineno) - node.lineno + 1

    def normalize_module_path(self, value: str) -> str:
        return value.replace(".", "/").strip("/")

    def import_path(self, node: ast.ImportFrom) -> str:
        return f"{'.' * node.level}{node.module or ''}"

    def path_parts(self, value: str) -> list[str]:
        return [part for part in value.replace("\\", "/").split("/") if part and part != "."]

    def relative_path_parts(self, path: str, sources_root: str) -> list[str]:
        path_parts = self.path_parts(path)
        root_parts = self.path_parts(sources_root)
        if path_parts[: len(root_parts)] == root_parts:
            return path_parts[len(root_parts) :]
        return path_parts[-1:]

    def normalized_import_path(self, import_value: str, is_relative: bool, file_path: str, sources_root: str) -> str:
        if not is_relative:
            return self.normalize_module_path(import_value)
        level = len(import_value) - len(import_value.lstrip("."))
        module = import_value[level:]
        package_parts = self.relative_path_parts(file_path, sources_root)[:-1]
        for _ in range(max(level - 1, 0)):
            if package_parts:
                package_parts.pop()
        package_path = "/".join(package_parts)
        module_path = self.normalize_module_path(module)
        return "/".join(part for part in (package_path, module_path) if part)

    def argument_counts(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, *, exclude_receiver: bool
    ) -> tuple[int, int]:
        positional_args = [*node.args.posonlyargs, *node.args.args]
        positional_required_count = len(positional_args) - len(node.args.defaults)
        parameters = [(arg.arg, index >= positional_required_count) for index, arg in enumerate(positional_args)]
        parameters.extend(
            (
                (arg.arg, default is not None)
                for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
            )
        )
        if node.args.vararg is not None:
            parameters.append((node.args.vararg.arg, True))
        if node.args.kwarg is not None:
            parameters.append((node.args.kwarg.arg, True))
        if exclude_receiver and parameters and (parameters[0][0] in {"self", "cls"}):
            parameters = parameters[1:]
        return (len(parameters), sum((1 for _, is_optional in parameters if is_optional)))

    def has_decorator(self, node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == name:
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr == name:
                return True
        return False

    def node_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent_name = self.node_name(node.value)
            return f"{parent_name}.{node.attr}" if parent_name else node.attr
        return ""

    def method_is_abstract(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return self.has_decorator(node, "abstractmethod")

    def class_is_abstract(self, node: ast.ClassDef) -> bool:
        return any(self.node_name(base) in {"ABC", "abc.ABC"} for base in node.bases) or any(
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and self.method_is_abstract(child)
            for child in node.body
        )

    def visibility_intent(self, name: str) -> str:
        if name.startswith("__") and (not (name.startswith("__") and name.endswith("__"))):
            return "private"
        if name.startswith("_") and (not (name.startswith("__") and name.endswith("__"))):
            return "protected"
        return "public"

    def annotation_is_optional(self, node: ast.AST | None) -> bool:
        if node is None:
            return False
        if isinstance(node, ast.Constant) and node.value is None:
            return True
        if isinstance(node, ast.Name):
            return node.id in {"None", "Optional"}
        if isinstance(node, ast.Attribute):
            return node.attr == "Optional"
        if isinstance(node, ast.Subscript):
            return self.annotation_is_optional(node.value) or self.annotation_is_optional(node.slice)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return self.annotation_is_optional(node.left) or self.annotation_is_optional(node.right)
        if isinstance(node, ast.Tuple):
            return any(self.annotation_is_optional(element) for element in node.elts)
        return False

    def value_is_none(self, node: ast.AST | None) -> bool:
        return isinstance(node, ast.Constant) and node.value is None

    def optional_constructor_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        positional_args = [*node.args.posonlyargs, *node.args.args]
        defaults_by_name = {}
        if node.args.defaults:
            defaults_by_name = {
                arg.arg: default
                for arg, default in zip(positional_args[-len(node.args.defaults) :], node.args.defaults, strict=True)
            }
        optional_names = {
            arg.arg for arg in [*positional_args, *node.args.kwonlyargs] if self.annotation_is_optional(arg.annotation)
        }
        optional_names.update((name for name, default in defaults_by_name.items() if self.value_is_none(default)))
        optional_names.update(
            (
                arg.arg
                for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
                if self.value_is_none(default)
            )
        )
        return optional_names

    def add_property(self, properties: dict[str, bool], name: str, is_optional: bool) -> None:
        properties[name] = properties.get(name, False) or is_optional

    def class_properties(self, node: ast.ClassDef) -> list[dict[str, object]]:
        properties: dict[str, bool] = {}

        for child in node.body:
            if isinstance(child, ast.AnnAssign):
                target = child.target
                if isinstance(target, ast.Name):
                    self.add_property(
                        properties,
                        target.id,
                        self.annotation_is_optional(child.annotation) or self.value_is_none(child.value),
                    )
                continue
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        self.add_property(properties, target.id, self.value_is_none(child.value))
                continue
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            optional_parameter_names = self.optional_constructor_parameters(child)
            for descendant in ast.walk(child):
                if isinstance(descendant, ast.AnnAssign):
                    target = descendant.target
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and (target.value.id in {"self", "cls"})
                    ):
                        self.add_property(
                            properties,
                            target.attr,
                            self.annotation_is_optional(descendant.annotation) or self.value_is_none(descendant.value),
                        )
                    continue
                if not isinstance(descendant, ast.Assign):
                    continue
                is_optional = self.value_is_none(descendant.value) or (
                    isinstance(descendant.value, ast.Name) and descendant.value.id in optional_parameter_names
                )
                for target in descendant.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and (target.value.id in {"self", "cls"})
                    ):
                        self.add_property(properties, target.attr, is_optional)
        return [{"name": name, "is_optional": is_optional} for name, is_optional in properties.items()]

    def method_definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, object]:
        declared_args, optional_args = self.argument_counts(
            node, exclude_receiver=not self.has_decorator(node, "staticmethod")
        )
        return {
            "name": node.name,
            "visibility": "public",
            "visibility_intent": self.visibility_intent(node.name),
            "line_count": self.line_span(node),
            "declared_args": declared_args,
            "optional_args": optional_args,
        }

    def class_definition(self, node: ast.ClassDef) -> dict[str, object]:
        return {
            "name": node.name,
            "visibility": "public",
            "visibility_intent": self.visibility_intent(node.name),
            "methods": [
                self.method_definition(child)
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ],
            "properties": self.class_properties(node),
            "line_count": self.line_span(node),
        }

    def abstract_class_definition(self, node: ast.ClassDef) -> dict[str, object]:
        methods = [
            self.method_definition(child)
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        abstract_method_names = {
            child.name
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and self.method_is_abstract(child)
        }
        return {
            "name": node.name,
            "visibility": "public",
            "visibility_intent": self.visibility_intent(node.name),
            "abstract_methods": [method for method in methods if method["name"] in abstract_method_names],
            "concrete_methods": [method for method in methods if method["name"] not in abstract_method_names],
            "properties": self.class_properties(node),
            "line_count": self.line_span(node),
        }

    def function_definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, object]:
        declared_args, optional_args = self.argument_counts(node, exclude_receiver=False)
        return {
            "name": node.name,
            "visibility": "public",
            "visibility_intent": self.visibility_intent(node.name),
            "line_count": self.line_span(node),
            "declared_args": declared_args,
            "optional_args": optional_args,
        }

    def source_id_for_path(self, path: str, sources_root: str) -> str:
        return "/".join(self.relative_path_parts(path, sources_root)).removesuffix(".py").strip("/")

    def callable_id(self, source_id: str, qualified_name: str) -> str:
        return f"{source_id}::{qualified_name}"

    def unparse(self, node: ast.AST | None) -> str:
        if node is None:
            return ""
        return ast.unparse(node)

    def parameter_details(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, *, exclude_receiver: bool
    ) -> list[dict[str, object]]:
        args = node.args
        positional_args = [*args.posonlyargs, *args.args]
        defaults = [None] * (len(positional_args) - len(args.defaults)) + list(args.defaults)
        parameters: list[dict[str, object]] = [
            {
                "name": arg.arg,
                "annotation": self.unparse(arg.annotation),
                "kind": "positional",
                "has_default": default is not None,
            }
            for arg, default in zip(positional_args, defaults, strict=True)
        ]
        if args.vararg is not None:
            parameters.append(
                {
                    "name": args.vararg.arg,
                    "annotation": self.unparse(args.vararg.annotation),
                    "kind": "vararg",
                    "has_default": True,
                }
            )
        parameters.extend(
            (
                {
                    "name": arg.arg,
                    "annotation": self.unparse(arg.annotation),
                    "kind": "keyword_only",
                    "has_default": default is not None,
                }
                for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True)
            )
        )
        if args.kwarg is not None:
            parameters.append(
                {
                    "name": args.kwarg.arg,
                    "annotation": self.unparse(args.kwarg.annotation),
                    "kind": "kwarg",
                    "has_default": True,
                }
            )
        if exclude_receiver and parameters and (parameters[0]["name"] in {"self", "cls"}):
            return parameters[1:]
        return parameters

    def callable_from_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, source_id: str, *, qualified_name: str, owner_name: str
    ) -> dict[str, object]:
        is_method = owner_name != ""
        if node.name == "__init__" and is_method:
            kind = "constructor"
        elif is_method and self.has_decorator(node, "classmethod"):
            kind = "classmethod"
        elif is_method and self.has_decorator(node, "staticmethod"):
            kind = "staticmethod"
        elif is_method:
            kind = "method"
        else:
            kind = "function"
        exclude_receiver = is_method and kind != "staticmethod"
        declared_args, optional_args = self.argument_counts(node, exclude_receiver=exclude_receiver)
        return {
            "id": self.callable_id(source_id, qualified_name),
            "source_id": source_id,
            "name": node.name,
            "qualified_name": qualified_name,
            "owner_name": owner_name,
            "kind": kind,
            "visibility": "public",
            "visibility_intent": self.visibility_intent(node.name),
            "line_start": node.lineno,
            "line_end": node.end_lineno,
            "line_count": self.line_span(node),
            "parameters": self.parameter_details(node, exclude_receiver=exclude_receiver),
            "declared_args": declared_args,
            "optional_args": optional_args,
            "return_annotation": self.unparse(node.returns),
            "decorators": [self.unparse(decorator) for decorator in node.decorator_list],
            "docstring": ast.get_docstring(node) or "",
        }

    def callable_from_lambda(
        self,
        node: ast.Lambda,
        source_id: str,
        *,
        qualified_name: str,
        name: str,
        owner_name: str,
        kind: str,
    ) -> dict[str, object]:
        parameters = self.parameter_details(node, exclude_receiver=False)
        return {
            "id": self.callable_id(source_id, qualified_name),
            "source_id": source_id,
            "name": name,
            "qualified_name": qualified_name,
            "owner_name": owner_name,
            "kind": kind,
            "visibility": "public",
            "visibility_intent": self.visibility_intent(name),
            "line_start": node.lineno,
            "line_end": node.end_lineno,
            "line_count": self.line_span(node),
            "parameters": parameters,
            "declared_args": len(parameters),
            "optional_args": sum(1 for parameter in parameters if parameter["has_default"]),
            "return_annotation": "",
            "decorators": [],
            "docstring": "",
        }

    def value_kind(self, node: ast.AST | None) -> str:
        if isinstance(node, ast.Lambda):
            return "callable"
        if isinstance(node, ast.Constant):
            return "literal"
        if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return "object"
        if isinstance(node, ast.Call):
            return "object"
        return "unknown"

    def source_value(self, name: str, node: ast.stmt, value: ast.AST | None) -> dict[str, object]:
        declared_args = 0
        optional_args = 0
        if isinstance(value, ast.Lambda):
            parameters = self.parameter_details(value, exclude_receiver=False)
            declared_args = len(parameters)
            optional_args = sum(1 for parameter in parameters if parameter["has_default"])
        return {
            "name": name,
            "visibility": "public",
            "visibility_intent": self.visibility_intent(name),
            "line_count": self.line_span(node),
            "declaration_kind": "assignment",
            "value_kind": self.value_kind(value),
            "declared_args": declared_args,
            "optional_args": optional_args,
        }

    def lambda_has_call(self, node: ast.Lambda) -> bool:
        return any(isinstance(descendant, ast.Call) for descendant in ast.walk(node))

    def collect_lambda_callables(
        self, root: ast.AST, source_id: str, *, parent_qualified_name: str, owner_name: str
    ) -> list[tuple[str, ast.Lambda, dict[str, object]]]:
        callables: list[tuple[str, ast.Lambda, dict[str, object]]] = []
        for node in ast.walk(root):
            if not isinstance(node, ast.Lambda) or node is root:
                continue
            if not self.lambda_has_call(node):
                continue
            name = f"<anonymous>@{node.lineno}:{node.col_offset}"
            qualified_name = f"{parent_qualified_name}.{name}"
            source_callable = self.callable_from_lambda(
                node, source_id, qualified_name=qualified_name, name=name, owner_name=owner_name, kind="anonymous"
            )
            callables.append((cast(str, source_callable["id"]), node, source_callable))
        return callables

    def collect_callable_graph(
        self, tree: ast.Module, source_id: str
    ) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
        values: list[dict[str, object]] = []
        callables: list[dict[str, object]] = []
        callable_nodes: list[tuple[str, ast.AST, str]] = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        values.append(self.source_value(target.id, node, node.value))
                        if isinstance(node.value, ast.Lambda):
                            qualified_name = target.id
                            source_callable = self.callable_from_lambda(
                                node.value,
                                source_id,
                                qualified_name=qualified_name,
                                name=target.id,
                                kind="callable_value",
                                owner_name="",
                            )
                            callables.append(source_callable)
                            callable_nodes.append((cast(str, source_callable["id"]), node.value, ""))
                continue
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                values.append(self.source_value(node.target.id, node, node.value))
                if isinstance(node.value, ast.Lambda):
                    qualified_name = node.target.id
                    source_callable = self.callable_from_lambda(
                        node.value,
                        source_id,
                        qualified_name=qualified_name,
                        name=node.target.id,
                        kind="callable_value",
                        owner_name="",
                    )
                    callables.append(source_callable)
                    callable_nodes.append((cast(str, source_callable["id"]), node.value, ""))
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                source_callable = self.callable_from_function(node, source_id, qualified_name=node.name, owner_name="")
                callables.append(source_callable)
                callable_nodes.append((cast(str, source_callable["id"]), node, ""))
                for anonymous_id, anonymous_node, anonymous_callable in self.collect_lambda_callables(
                    node, source_id, parent_qualified_name=node.name, owner_name=""
                ):
                    callables.append(anonymous_callable)
                    callable_nodes.append((anonymous_id, anonymous_node, ""))
                continue
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    qualified_name = f"{node.name}.{child.name}"
                    source_callable = self.callable_from_function(
                        child, source_id, qualified_name=qualified_name, owner_name=node.name
                    )
                    callables.append(source_callable)
                    callable_nodes.append((cast(str, source_callable["id"]), child, node.name))
                    for anonymous_id, anonymous_node, anonymous_callable in self.collect_lambda_callables(
                        child, source_id, parent_qualified_name=qualified_name, owner_name=node.name
                    ):
                        callables.append(anonymous_callable)
                        callable_nodes.append((anonymous_id, anonymous_node, node.name))
        by_qualified_name = {
            str(source_callable["qualified_name"]): str(source_callable["id"]) for source_callable in callables
        }
        by_name = {
            str(source_callable["name"]): str(source_callable["id"])
            for source_callable in callables
            if source_callable["kind"] in {"function", "callable_value"}
        }
        constructors_by_name = {
            str(source_callable["owner_name"]): str(source_callable["id"])
            for source_callable in callables
            if source_callable["kind"] == "constructor"
        }
        calls: list[dict[str, object]] = []
        for source_callable_id, node, owner_name in callable_nodes:
            context = PythonCallContext(
                source_id=source_id,
                source_callable_id=source_callable_id,
                owner_name=owner_name,
                by_name=by_name,
                by_qualified_name=by_qualified_name,
                constructors_by_name=constructors_by_name,
            )
            if isinstance(node, ast.Lambda):
                calls.extend(self.calls.collect(node.body, context))
            else:
                for child in getattr(node, "body", []):
                    calls.extend(self.calls.collect(child, context))
        return (values, callables, calls)

    def code_line_count(self, content: str) -> int:
        return sum(1 for line in content.splitlines() if line.strip() and (not line.strip().startswith("#")))

    def import_join_key(self, import_path_value: str) -> str:
        return self.normalize_module_path(import_path_value).rsplit("/", 1)[0]

    def imported_symbol(self, alias: ast.alias) -> dict[str, object]:
        return {
            "name": alias.name,
            "alias": alias.asname or "",
            "is_aliased": alias.asname is not None,
            "is_default": False,
            "is_namespace": False,
            "is_star": alias.name == "*",
        }

    def collect_imports(self, tree: ast.Module, path: str, sources_root: str) -> list[dict[str, object]]:
        imports: list[dict[str, object]] = []
        for statement_id, node in enumerate(ast.walk(tree), start=1):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "path": alias.name,
                            "is_relative": False,
                            "normalized_path": self.normalized_import_path(alias.name, False, path, sources_root),
                            "imported_name": "",
                            "is_aliased": alias.asname is not None,
                            "crossing_type": "module",
                            "file_barrier_crossed": True,
                            "statement_id": statement_id,
                            "join_key": self.import_join_key(alias.name),
                            "uses_joined_import": False,
                            "imported_symbols": [],
                        }
                    )
                continue
            if isinstance(node, ast.ImportFrom):
                node_path = self.import_path(node)
                for alias in node.names:
                    imports.append(
                        {
                            "path": node_path,
                            "is_relative": node.level > 0,
                            "normalized_path": self.normalized_import_path(
                                node_path, node.level > 0, path, sources_root
                            ),
                            "imported_name": alias.name,
                            "is_aliased": alias.asname is not None,
                            "crossing_type": "symbol",
                            "file_barrier_crossed": True,
                            "statement_id": statement_id,
                            "join_key": node_path,
                            "uses_joined_import": True,
                            "imported_symbols": [self.imported_symbol(alias)],
                        }
                    )
        return imports

    def static_all_names(self, tree: ast.Module) -> set[str] | None:
        names: set[str] | None = None
        for node in tree.body:
            value = None
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            ):
                value = node.value
            elif (
                isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and (node.target.id == "__all__")
            ):
                value = node.value
            if value is None:
                continue
            if not isinstance(value, (ast.List, ast.Tuple)):
                return None
            names = set()
            for element in value.elts:
                if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                    return None
                names.add(element.value)
        return names

    def export_entry(
        self,
        name: str,
        kind: str,
        *,
        local_name: str,
        path: str,
        is_relative: bool,
        normalized_path: str,
        is_reexport: bool,
        is_aliased: bool,
        statement_id: int,
    ) -> dict[str, object]:
        return {
            "name": name,
            "local_name": local_name,
            "kind": kind,
            "crossing_type": "symbol",
            "path": path,
            "is_relative": is_relative,
            "normalized_path": normalized_path,
            "is_reexport": is_reexport,
            "is_default": False,
            "is_aliased": is_aliased,
            "statement_id": statement_id,
        }

    def direct_export_entry(self, name: str, kind: str) -> dict[str, object]:
        return self.export_entry(
            name,
            kind,
            local_name=name,
            path="",
            is_relative=False,
            normalized_path="",
            is_reexport=False,
            is_aliased=False,
            statement_id=0,
        )

    def collect_exports(
        self,
        tree: ast.Module,
        path: str,
        sources_root: str,
        classes: list[dict[str, object]],
        abstract_classes: list[dict[str, object]],
        functions: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        declaration_exports = {
            **{
                str(class_definition["name"]): self.export_entry(
                    str(class_definition["name"]),
                    "class",
                    local_name=str(class_definition["name"]),
                    path="",
                    is_relative=False,
                    normalized_path="",
                    is_reexport=False,
                    is_aliased=False,
                    statement_id=0,
                )
                for class_definition in classes
            },
            **{
                str(class_definition["name"]): self.export_entry(
                    str(class_definition["name"]),
                    "abstract_class",
                    local_name=str(class_definition["name"]),
                    path="",
                    is_relative=False,
                    normalized_path="",
                    is_reexport=False,
                    is_aliased=False,
                    statement_id=0,
                )
                for class_definition in abstract_classes
            },
            **{
                str(function_definition["name"]): self.export_entry(
                    str(function_definition["name"]),
                    "function",
                    local_name=str(function_definition["name"]),
                    path="",
                    is_relative=False,
                    normalized_path="",
                    is_reexport=False,
                    is_aliased=False,
                    statement_id=0,
                )
                for function_definition in functions
            },
        }
        import_exports: dict[str, dict[str, object]] = {}
        for statement_id, node in enumerate(ast.walk(tree), start=1):
            if not isinstance(node, ast.ImportFrom):
                continue
            node_path = self.import_path(node)
            for alias in node.names:
                exported_name = alias.asname or alias.name
                import_exports[exported_name] = self.export_entry(
                    exported_name,
                    "unknown",
                    local_name=alias.name,
                    path=node_path,
                    is_relative=node.level > 0,
                    normalized_path=self.normalized_import_path(node_path, node.level > 0, path, sources_root),
                    is_reexport=True,
                    is_aliased=alias.asname is not None,
                    statement_id=statement_id,
                )
        explicit_names = self.static_all_names(tree)
        if explicit_names is None:
            return [source_export for name, source_export in declaration_exports.items() if not name.startswith("_")]
        exports: list[dict[str, object]] = []
        for name in sorted(explicit_names):
            if name in import_exports:
                exports.append(import_exports[name])
                continue
            exports.append(declaration_exports.get(name, self.direct_export_entry(name, "unknown")))
        return exports

    def extract(self, content: str, path: str, sources_root: str, source_id: str | None) -> dict[str, object]:
        tree = ast.parse(content, filename=str(path))
        resolved_source_id = source_id or self.source_id_for_path(path, sources_root)
        class_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        classes = [self.class_definition(node) for node in class_nodes if not self.class_is_abstract(node)]
        abstract_classes = [
            self.abstract_class_definition(node) for node in class_nodes if self.class_is_abstract(node)
        ]
        functions = [
            self.function_definition(node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        values, callables, calls = self.collect_callable_graph(tree, resolved_source_id)
        return {
            "imports": self.collect_imports(tree, path, sources_root),
            "exports": self.collect_exports(tree, path, sources_root, classes, abstract_classes, functions),
            "classes": classes,
            "interfaces": [],
            "types": [],
            "abstract_classes": abstract_classes,
            "functions": functions,
            "values": values,
            "callables": callables,
            "calls": calls,
            "line_count": len(content.splitlines()),
            "code_line_count": self.code_line_count(content),
            "public_symbol_count": sum(
                1
                for node in tree.body
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and (not node.name.startswith("_"))
            ),
        }
