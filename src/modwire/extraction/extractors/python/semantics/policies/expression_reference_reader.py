import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ...observations.inheritance_candidate import PythonInheritanceCandidate


class PythonExpressionReferenceReader(ABC):
    @abstractmethod
    def read(self, candidate: PythonInheritanceCandidate) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_expression(self, node: ast.expr) -> str:
        raise NotImplementedError


@injectable(as_type=PythonExpressionReferenceReader)
@dataclass(frozen=True)
class SyntaxExpressionReferenceReader(PythonExpressionReferenceReader):
    def read(self, candidate: PythonInheritanceCandidate) -> str:
        return ast.unparse(candidate.base)

    def read_expression(self, node: ast.expr) -> str:
        return self.visit(node)

    @singledispatchmethod
    def visit(self, node: ast.expr) -> str:
        return ""

    @visit.register
    def visit_Name(self, node: ast.Name) -> str:
        return node.id

    @visit.register
    def visit_Attribute(self, node: ast.Attribute) -> str:
        parent = self.read_expression(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
