import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonPropertyCandidate:
    statement: ast.Assign | ast.AnnAssign | ast.FunctionDef | ast.AsyncFunctionDef
    binding_scope: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    name: str
    source_span: tuple[int, int]
    ordinal: int
    target: ast.Name | ast.Attribute | ast.FunctionDef | ast.AsyncFunctionDef
