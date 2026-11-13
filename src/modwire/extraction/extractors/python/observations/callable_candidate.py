import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonCallableCandidate:
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    identity_node: ast.stmt | ast.expr
    binding_scope: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    name: str
    qualified_name: str
    ordinal: int
    root_ordinal: int
    sequence: int
    source_span: tuple[int, int]
