import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonValueCandidate:
    statement: ast.Assign | ast.AnnAssign
    target: ast.Name
    ordinal: int
