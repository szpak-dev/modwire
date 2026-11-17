import ast
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_placement import SourcePlacement
from ......shared.code.models.source_types.absent import SourceTypeAbsent
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ......shared.code.models.values.source_member_kind import SourceMemberKind
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.property_candidate import PythonPropertyCandidate
from ..policies.assigned_value_reader import PythonAssignedValueReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from .classifier import PythonPropertyRule


@injectable(as_type=PythonPropertyRule, qualifier="40-assigned-instance")
@dataclass(frozen=True)
class AssignedInstancePropertyRule(PythonPropertyRule):
    assigned_values: PythonAssignedValueReader
    visibility: PythonVisibilityPolicy

    @cached_property
    def is_assignment_dispatch(self) -> Callable[[ast.stmt], bool]:
        return self.is_assignment

    @cached_property
    def read_dispatch(
        self,
    ) -> Callable[
        [
            ast.stmt,
            PythonPropertyCandidate,
            DeclarationIdentity,
            DeclarationIdentity,
            SourceMemberKind,
            SourcePlacement,
        ],
        SourceClassProperty,
    ]:
        return self.read

    @property
    def order(self) -> int:
        return 40

    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        return not self.is_class_target_dispatch(candidate.target) and self.is_assignment_dispatch(candidate.statement)

    def classify(
        self,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        return self.read_dispatch(
            candidate.statement, candidate, declaration_id, owner_declaration_id, member_kind, placement
        )

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
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        raise ExtractorInvariantError(
            ExtractorInvariantViolation.ASSIGNED_INSTANCE_PROPERTY_REQUIRES_ASSIGNMENT, candidate.name
        )

    @read.register
    def read_assignment(
        self,
        statement: ast.Assign,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        optional_parameters = self.optional_parameters_dispatch(candidate.binding_scope)
        return self.build(
            candidate=candidate,
            declaration_id=declaration_id,
            owner_declaration_id=owner_declaration_id,
            is_optional=self.value_is_none_dispatch(statement.value)
            or self.expression_name_dispatch(statement.value) in optional_parameters,
            type=SourceTypeAbsent(),
            visibility=self.visibility.classify(candidate.name),
            member_kind=member_kind,
            placement=placement,
            assigned_value=self.assigned_values.read_expression(statement.value),
        )
