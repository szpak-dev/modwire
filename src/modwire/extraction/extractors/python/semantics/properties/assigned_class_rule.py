import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_member_kind import SourceMemberKind
from ......shared.code.models.source_types.absent import SourceTypeAbsent
from ......shared.code.models.source_types.reference import SourceTypeReference
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.property_candidate import PythonPropertyCandidate
from ...observations.property_scope import PythonPropertyScope
from ..policies.assigned_value_reader import PythonAssignedValueReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from .classifier import PythonPropertyRule


@injectable(as_type=PythonPropertyRule, qualifier="20-assigned-class")
@dataclass(frozen=True)
class AssignedClassPropertyRule(PythonPropertyRule):
    assigned_values: PythonAssignedValueReader
    visibility: PythonVisibilityPolicy

    @property
    def order(self) -> int:
        return 20

    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        return candidate.scope is PythonPropertyScope.CLASS and self.is_assignment(candidate.statement)

    def classify(
        self,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        return self.read(candidate.statement, candidate, declaration_id, owner_declaration_id)

    @singledispatchmethod
    def is_assignment(self, statement: ast.stmt) -> bool:
        return False

    @is_assignment.register
    def assignment_is_assignment(self, statement: ast.Assign) -> bool:
        return True

    @singledispatchmethod
    def read(
        self,
        statement: ast.stmt,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        raise ExtractorInvariantError(
            ExtractorInvariantViolation.ASSIGNED_CLASS_PROPERTY_REQUIRES_ASSIGNMENT, candidate.name
        )

    @read.register
    def read_assignment(
        self,
        statement: ast.Assign,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        return self.build(
            candidate=candidate,
            declaration_id=declaration_id,
            owner_declaration_id=owner_declaration_id,
            is_optional=self.value_is_none(statement.value),
            type=self.source_type(candidate),
            visibility=self.visibility.classify(candidate.name),
            member_kind=SourceMemberKind.STATIC,
            assigned_value=self.assigned_values.read_expression(statement.value),
        )

    def source_type(self, candidate: PythonPropertyCandidate) -> SourceTypeReference | SourceTypeAbsent:
        if any(ast.unparse(base).rsplit(".", 1)[-1] == "StrEnum" for base in candidate.class_bases):
            return SourceTypeReference(name="str")
        return SourceTypeAbsent()
