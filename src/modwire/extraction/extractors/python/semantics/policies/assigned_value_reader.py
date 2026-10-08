import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_assigned_value import SourceAssignedValue
from ......shared.code.models.source_assigned_value_kind import SourceAssignedValueKind
from ...observations.value_candidate import PythonValueCandidate
from .expression_reference_reader import PythonExpressionReferenceReader


class PythonAssignedValueReader(ABC):
    @abstractmethod
    def read(self, candidate: PythonValueCandidate) -> SourceAssignedValue:
        raise NotImplementedError

    @abstractmethod
    def read_expression(self, node: ast.expr) -> SourceAssignedValue:
        raise NotImplementedError

    @abstractmethod
    def unassigned(self) -> SourceAssignedValue:
        raise NotImplementedError


@injectable(as_type=PythonAssignedValueReader)
@dataclass(frozen=True)
class SyntaxAssignedValueReader(PythonAssignedValueReader):
    references: PythonExpressionReferenceReader

    def read(self, candidate: PythonValueCandidate) -> SourceAssignedValue:
        return self.read_statement(candidate.statement)

    @singledispatchmethod
    def read_statement(self, statement: ast.stmt) -> SourceAssignedValue:
        raise ValueError("Unsupported Python value statement.")

    @read_statement.register
    def read_assignment(self, statement: ast.Assign) -> SourceAssignedValue:
        return self.read_expression(statement.value)

    @read_statement.register
    def read_annotated_assignment(self, statement: ast.AnnAssign) -> SourceAssignedValue:
        if statement.value is None:
            return self.unassigned()
        return self.read_expression(statement.value)

    def read_expression(self, node: ast.expr) -> SourceAssignedValue:
        return self.visit(node)

    def unassigned(self) -> SourceAssignedValue:
        return SourceAssignedValue(kind=SourceAssignedValueKind.UNASSIGNED, expression="", reference="")

    @singledispatchmethod
    def visit(self, node: ast.expr) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.UNRESOLVED,
            expression=ast.unparse(node),
            reference="",
        )

    @visit.register
    def visit_Call(self, node: ast.Call) -> SourceAssignedValue:
        expression = ast.unparse(node)
        reference = self.references.read_expression(node.func)
        if not reference:
            return SourceAssignedValue(kind=SourceAssignedValueKind.UNRESOLVED, expression=expression, reference="")
        return SourceAssignedValue(kind=SourceAssignedValueKind.CALL, expression=expression, reference=reference)

    @visit.register
    def visit_Name(self, node: ast.Name) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.REFERENCE,
            expression=ast.unparse(node),
            reference=self.references.read_expression(node),
        )

    @visit.register
    def visit_Attribute(self, node: ast.Attribute) -> SourceAssignedValue:
        reference = self.references.read_expression(node)
        if not reference:
            return SourceAssignedValue(
                kind=SourceAssignedValueKind.UNRESOLVED,
                expression=ast.unparse(node),
                reference="",
            )
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.REFERENCE,
            expression=ast.unparse(node),
            reference=reference,
        )

    @visit.register
    def visit_Constant(self, node: ast.Constant) -> SourceAssignedValue:
        return self.literal(node)

    @visit.register
    def visit_List(self, node: ast.List) -> SourceAssignedValue:
        return self.literal(node)

    @visit.register
    def visit_Tuple(self, node: ast.Tuple) -> SourceAssignedValue:
        return self.literal(node)

    @visit.register
    def visit_Set(self, node: ast.Set) -> SourceAssignedValue:
        return self.literal(node)

    @visit.register
    def visit_Dict(self, node: ast.Dict) -> SourceAssignedValue:
        return self.literal(node)

    def literal(self, node: ast.expr) -> SourceAssignedValue:
        return SourceAssignedValue(
            kind=SourceAssignedValueKind.LITERAL,
            expression=ast.unparse(node),
            reference="",
        )
