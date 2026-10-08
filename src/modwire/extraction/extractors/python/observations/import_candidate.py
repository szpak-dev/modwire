import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonImportCandidate:
    node: ast.Import | ast.ImportFrom
    alias: ast.alias
    path: str
    is_relative: bool
    statement_id: int
