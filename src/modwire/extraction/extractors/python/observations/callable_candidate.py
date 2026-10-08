import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonCallableCandidate:
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    identity_node: ast.stmt | ast.expr
    name: str
    qualified_name: str
    owner_name: str
    ordinal: int
    requires_call: bool
    root_ordinal: int
    sequence: int
