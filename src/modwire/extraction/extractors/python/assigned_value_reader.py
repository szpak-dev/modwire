import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ....shared.code.models.source_assigned_value import SourceAssignedValue
from ....shared.code.models.source_assigned_value_kind import SourceAssignedValueKind
from .domain import PythonAssignedValueReader, PythonExpressionReferenceReader


@injectable(as_type=PythonAssignedValueReader)
@dataclass(frozen=True)
class SyntaxAssignedValueReader(PythonAssignedValueReader):
    references: PythonExpressionReferenceReader

    def read(self, node: ast.expr) -> SourceAssignedValue:
        return self.visit(node)

    def unassigned(self) -> SourceAssignedValue:
        return SourceAssignedValue(kind=SourceAssignedValueKind.UNASSIGNED, expression="", reference="")

    @singledispatchmethod
    def visit(self, node: ast.AST) -> SourceAssignedValue:
        return self.generic_visit(node)

    @visit.register
    def visit_Call(self, node: ast.Call) -> SourceAssignedValue:
        expression = ast.unparse(node)
        reference = self.references.read(node.func)
        if not reference:
            return SourceAssignedValue(
                kind=SourceAssignedValueKind.UNRESOLVED,
                expression=expression,
                reference="",
            )
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.CALL,
            expression=expression,
            reference=reference,
        )

    @visit.register
    def visit_Name(self, node: ast.Name) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.REFERENCE,
            expression=ast.unparse(node),
            reference=self.references.read(node),
        )

    @visit.register
    def visit_Attribute(self, node: ast.Attribute) -> SourceAssignedValue:
        reference = self.references.read(node)
        if not reference:
            return self.generic_visit(node)
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.REFERENCE,
            expression=ast.unparse(node),
            reference=reference,
        )

    @visit.register
    def visit_Constant(self, node: ast.Constant) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.LITERAL,
            expression=ast.unparse(node),
            reference="",
        )

    @visit.register
    def visit_List(self, node: ast.List) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.LITERAL,
            expression=ast.unparse(node),
            reference="",
        )

    @visit.register
    def visit_Tuple(self, node: ast.Tuple) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.LITERAL,
            expression=ast.unparse(node),
            reference="",
        )

    @visit.register
    def visit_Set(self, node: ast.Set) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.LITERAL,
            expression=ast.unparse(node),
            reference="",
        )

    @visit.register
    def visit_Dict(self, node: ast.Dict) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.LITERAL,
            expression=ast.unparse(node),
            reference="",
        )

    def generic_visit(self, node: ast.AST) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.UNRESOLVED,
            expression=ast.unparse(node),
            reference="",
        )
