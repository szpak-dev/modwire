import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonTraversalContext:
    binding_scope: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    qualified_name: str
