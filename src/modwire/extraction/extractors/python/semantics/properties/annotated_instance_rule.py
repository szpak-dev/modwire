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


@injectable(as_type=PythonPropertyRule, qualifier="30-annotated-instance")
@dataclass(frozen=True)
class AnnotatedInstancePropertyRule(PythonPropertyRule):
    assigned_values: PythonAssignedValueReader
    visibility: PythonVisibilityPolicy

    @property
    def order(self) -> int:
        return 30

    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        return candidate.scope is PythonPropertyScope.METHOD and self.is_annotated(candidate.statement)

    def classify(self, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        return self.read(candidate.statement, candidate)

    @singledispatchmethod
    def is_annotated(self, statement: ast.stmt) -> bool:
        return False

    @is_annotated.register
    def annotated_is_annotated(self, statement: ast.AnnAssign) -> bool:
        return True

    @singledispatchmethod
    def read(self, statement: ast.stmt, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        raise ValueError("Annotated instance property requires an annotated assignment.")

    @read.register
    def read_annotated(self, statement: ast.AnnAssign, candidate: PythonPropertyCandidate) -> SourceClassProperty:
        assigned = self.assigned_values.unassigned()
        value_is_none = False
        if statement.value is not None:
            assigned = self.assigned_values.read_expression(statement.value)
            value_is_none = self.value_is_none(statement.value)
        member_kind = SourceMemberKind.INSTANCE if candidate.receiver == "self" else SourceMemberKind.STATIC
        return self.build(
            candidate=candidate,
            is_optional=self.annotation_is_optional(statement.annotation) or value_is_none,
            annotation=ast.unparse(statement.annotation),
            visibility=self.visibility.classify(candidate.name),
            member_kind=member_kind,
            assigned_value=assigned,
        )
