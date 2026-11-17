import ast
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_placement import SourcePlacement
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ......shared.code.models.values.source_member_kind import SourceMemberKind
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.property_candidate import PythonPropertyCandidate
from ..policies.assigned_value_reader import PythonAssignedValueReader
from ..policies.source_type_reader import PythonSourceTypeReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from .classifier import PythonPropertyRule


@injectable(as_type=PythonPropertyRule, qualifier="10-annotated-class")
@dataclass(frozen=True)
class AnnotatedClassPropertyRule(PythonPropertyRule):
    assigned_values: PythonAssignedValueReader
    visibility: PythonVisibilityPolicy
    types: PythonSourceTypeReader

    @cached_property
    def is_annotated_dispatch(self) -> Callable[[ast.stmt], bool]:
        return self.is_annotated

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
        return 10

    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        return self.is_class_target_dispatch(candidate.target) and self.is_annotated_dispatch(candidate.statement)

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
    def is_annotated(self, statement: ast.stmt) -> bool:
        return False

    @is_annotated.register
    def annotated_is_annotated(self, statement: ast.AnnAssign) -> bool:
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
            ExtractorInvariantViolation.ANNOTATED_CLASS_PROPERTY_REQUIRES_ANNOTATED_ASSIGNMENT,
            candidate.name,
        )

    @read.register
    def read_annotated(
        self,
        statement: ast.AnnAssign,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        assigned = self.assigned_values.unassigned()
        value_is_none = False
        if statement.value is not None:
            assigned = self.assigned_values.read_expression(statement.value)
            value_is_none = self.value_is_none_dispatch(statement.value)
        return self.build(
            candidate=candidate,
            declaration_id=declaration_id,
            owner_declaration_id=owner_declaration_id,
            is_optional=self.annotation_is_optional_dispatch(statement.annotation) or value_is_none,
            type=self.types.read(statement.annotation),
            visibility=self.visibility.classify(candidate.name),
            member_kind=member_kind,
            placement=placement,
            assigned_value=assigned,
        )
