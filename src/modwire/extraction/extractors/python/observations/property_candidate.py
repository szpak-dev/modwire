import ast
from dataclasses import dataclass

from .property_scope import PythonPropertyScope


@dataclass(frozen=True)
class PythonPropertyCandidate:
    statement: ast.Assign | ast.AnnAssign
    class_name: str
    class_line: int
    class_column: int
    method: ast.FunctionDef | ast.AsyncFunctionDef | ast.Module
    name: str
    receiver: str
    scope: PythonPropertyScope
