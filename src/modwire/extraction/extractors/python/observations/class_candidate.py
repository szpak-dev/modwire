import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PythonClassCandidate:
    node: ast.ClassDef
    ordinal: int
    module_level: bool
