import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ...observations.value_candidate import PythonValueCandidate
from .expression_reference_reader import PythonExpressionReferenceReader


class PythonTypeAliasClassifier(ABC):
    @abstractmethod
    def is_alias(self, candidate: PythonValueCandidate) -> bool:
        raise NotImplementedError


@injectable(as_type=PythonTypeAliasClassifier)
@dataclass(frozen=True)
class SyntaxTypeAliasClassifier(PythonTypeAliasClassifier):
    references: PythonExpressionReferenceReader

    def is_alias(self, candidate: PythonValueCandidate) -> bool:
        return self.statement_is_alias(candidate.statement)

    @singledispatchmethod
    def statement_is_alias(self, statement: ast.stmt) -> bool:
        raise ValueError("Unsupported Python value statement.")

    @statement_is_alias.register
    def assignment_is_alias(self, statement: ast.Assign) -> bool:
        return self.expression_is_alias(statement.value)

    @statement_is_alias.register
    def annotated_assignment_is_alias(self, statement: ast.AnnAssign) -> bool:
        if self.references.read_expression(statement.annotation).rsplit(".", 1)[-1] == "TypeAlias":
            return True
        if statement.value is None:
            return False
        return self.expression_is_alias(statement.value)

    @singledispatchmethod
    def expression_is_alias(self, expression: ast.expr) -> bool:
        return False

    @expression_is_alias.register
    def subscript_is_alias(self, expression: ast.Subscript) -> bool:
        return self.reference_tail(expression.value) in {"Annotated", "Callable", "Literal", "Optional", "Union"}

    @expression_is_alias.register
    def call_is_alias(self, expression: ast.Call) -> bool:
        return self.reference_tail(expression.func) in {
            "NewType",
            "ParamSpec",
            "TypeAliasType",
            "TypeVar",
            "TypeVarTuple",
        }

    def reference_tail(self, expression: ast.expr) -> str:
        reference = self.references.read_expression(expression)
        return reference.rsplit(".", 1)[-1]
