import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonFunctionCandidate:
    node: ast.FunctionDef | ast.AsyncFunctionDef
    ordinal: int
