import ast
from dataclasses import dataclass

from .class_candidate import PythonClassCandidate


@dataclass(frozen=True)
class PythonInheritanceCandidate:
    source: PythonClassCandidate
    base: ast.expr
