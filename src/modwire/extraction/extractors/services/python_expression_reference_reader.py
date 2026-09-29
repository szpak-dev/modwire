import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ..domain import PythonExpressionReferenceReader


@injectable(as_type=PythonExpressionReferenceReader)
@dataclass(frozen=True)
class SyntaxExpressionReferenceReader(PythonExpressionReferenceReader):
    def read(self, node: ast.expr) -> str:
        return self.visit(node)

    @singledispatchmethod
    def visit(self, node: ast.AST) -> str:
        return self.generic_visit(node)

    @visit.register
    def visit_Name(self, node: ast.Name) -> str:
        return node.id

    @visit.register
    def visit_Attribute(self, node: ast.Attribute) -> str:
        parent = self.read(node.value)
        return f"{parent}.{node.attr}" if parent else ""

    def generic_visit(self, node: ast.AST) -> str:
        return ""
