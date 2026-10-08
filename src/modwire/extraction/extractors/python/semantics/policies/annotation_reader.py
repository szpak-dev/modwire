import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ...observations.callable_candidate import PythonCallableCandidate


class PythonAnnotationReader(ABC):
    @abstractmethod
    def read(self, candidate: PythonCallableCandidate) -> str:
        raise NotImplementedError


@injectable(as_type=PythonAnnotationReader)
@dataclass(frozen=True)
class SyntaxAnnotationReader(PythonAnnotationReader):
    def read(self, candidate: PythonCallableCandidate) -> str:
        return self.visit(candidate.node)

    @singledispatchmethod
    def visit(self, node: ast.AST) -> str:
        return ""

    @visit.register
    def visit_FunctionDef(self, node: ast.FunctionDef) -> str:
        return self.return_annotation(node)

    @visit.register
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> str:
        return self.return_annotation(node)

    def return_annotation(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        if node.returns is None:
            return ""
        return ast.unparse(node.returns)
