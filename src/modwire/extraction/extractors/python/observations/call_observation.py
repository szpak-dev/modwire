import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonCallObservation:
    node: ast.Call
    source_qualified_name: str
    owner_name: str
