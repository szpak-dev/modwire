import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonCallObservation:
    node: ast.Call
    ordinal: int
    source_callable: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    binding_scope: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
