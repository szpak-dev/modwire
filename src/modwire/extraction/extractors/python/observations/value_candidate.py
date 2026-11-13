import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonValueCandidate:
    statement: ast.Assign | ast.AnnAssign | ast.TypeAlias
    target: ast.Name
    binding_scope: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    qualified_name: str
    ordinal: int
    source_span: tuple[int, int]
