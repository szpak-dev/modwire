import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonCallObservation:
    node: ast.Call
    ordinal: int
    source_qualified_name: str
    source_ordinal: int
    owner_name: str
