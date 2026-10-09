import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_class_property import SourceClassProperty
from ......shared.code.models.source_member_kind import SourceMemberKind
from ...observations.property_candidate import PythonPropertyCandidate
from ...observations.property_scope import PythonPropertyScope
from ..policies.assigned_value_reader import PythonAssignedValueReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from .classifier import PythonPropertyRule


@injectable(as_type=PythonPropertyRule, qualifier="40-assigned-instance")
@dataclass(frozen=True)
class AssignedInstancePropertyRule(PythonPropertyRule):
    assigned_values: PythonAssignedValueReader
    visibility: PythonVisibilityPolicy

    @property
    def order(self) -> int:
        return 40

    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        return candidate.scope is PythonPropertyScope.METHOD and self.is_assignment(candidate.statement)

    def classify(self, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        return self.read(candidate.statement, candidate)

    @singledispatchmethod
    def is_assignment(self, statement: ast.stmt) -> bool:
        return False

    @is_assignment.register
    def assignment_is_assignment(self, statement: ast.Assign) -> bool:
        return True

    @singledispatchmethod
    def read(self, statement: ast.stmt, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        raise ValueError("Assigned instance property requires an assignment.")

    @read.register
    def read_assignment(self, statement: ast.Assign, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        optional_parameters = self.optional_parameters(candidate.method)
        member_kind = SourceMemberKind.INSTANCE if candidate.receiver == "self" else SourceMemberKind.STATIC
        return self.build(
            candidate=candidate,
            is_optional=self.value_is_none(statement.value)
            or self.expression_name(statement.value) in optional_parameters,
            annotation="",
            visibility=self.visibility.classify(candidate.name),
            member_kind=member_kind,
            assigned_value=self.assigned_values.read_expression(statement.value),
        )
