import ast
from dataclasses import dataclass

from wireup import injectable

from ..domain import PythonCallReader
from ..models.python_call_context import PythonCallContext


@injectable(as_type=PythonCallReader)
@dataclass(frozen=True)
class SyntaxCallReader(PythonCallReader):
    def collect(self, node: ast.AST, context: PythonCallContext) -> list[dict[str, object]]:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return []
        calls: list[dict[str, object]] = []
        if isinstance(node, ast.Call):
            expression = ast.unparse(node.func)
            target_name = self._node_name(node.func) or expression
            target, resolution = self._resolve(node.func, expression, context)
            calls.append(
                {
                    "source_callable_id": context.source_callable_id,
                    "target_callable_id": target,
                    "source_id": context.source_id,
                    "line": node.lineno,
                    "expression": expression,
                    "resolution": resolution,
                    "target_name": target_name,
                }
            )
        for child in ast.iter_child_nodes(node):
            calls.extend(self.collect(child, context))
        return calls

    def _node_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._node_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    def _resolve(self, func: ast.AST, expression: str, context: PythonCallContext) -> tuple[str, str]:
        if expression in context.by_qualified_name:
            return (context.by_qualified_name[expression], "resolved")
        if isinstance(func, ast.Name):
            if func.id in context.by_name:
                return (context.by_name[func.id], "resolved")
            if func.id in context.constructors_by_name:
                return (context.constructors_by_name[func.id], "resolved")
            return ("", "unresolved")
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id in {"self", "cls"}:
                qualified = ".".join(part for part in (context.owner_name, func.attr) if part)
                if qualified in context.by_qualified_name:
                    return (context.by_qualified_name[qualified], "resolved")
            if func.attr in context.constructors_by_name:
                return (context.constructors_by_name[func.attr], "resolved")
            return ("", "unresolved")
        return ("", "dynamic")
