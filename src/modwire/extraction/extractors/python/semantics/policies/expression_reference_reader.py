import ast
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ...observations.declaration_relation_candidate import PythonDeclarationRelationCandidate


class PythonExpressionReferenceReader(ABC):
    @abstractmethod
    def read(self, candidate: PythonDeclarationRelationCandidate) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_expression(self, node: ast.expr) -> str:
        raise NotImplementedError


@injectable(as_type=PythonExpressionReferenceReader)
@dataclass(frozen=True)
class SyntaxExpressionReferenceReader(PythonExpressionReferenceReader):
    @cached_property
    def visit_dispatch(self) -> Callable[[ast.expr], str]:
        return self.visit

    def read(self, candidate: PythonDeclarationRelationCandidate) -> str:
        return ast.unparse(candidate.base)

    def read_expression(self, node: ast.expr) -> str:
        return self.visit_dispatch(node)

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
