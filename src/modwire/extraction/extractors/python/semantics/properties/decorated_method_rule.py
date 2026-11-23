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


@injectable(as_type=PythonPropertyRule, qualifier="50-decorated-method")
@dataclass(frozen=True)
class DecoratedMethodPropertyRule(PythonPropertyRule):
    assigned_values: PythonAssignedValueReader
    visibility: PythonVisibilityPolicy
    types: PythonSourceTypeReader

    @cached_property
    def is_observed_method_dispatch(self) -> Callable[[ast.stmt], bool]:
        return self.is_observed_method

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
        return 50

    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        return self.is_observed_method_dispatch(candidate.statement)

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
    def is_observed_method(self, statement: ast.stmt) -> bool:
        return False

    @is_observed_method.register(ast.FunctionDef)
    @is_observed_method.register(ast.AsyncFunctionDef)
    def observed_method(self, statement: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
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
            ExtractorInvariantViolation.DECORATED_METHOD_PROPERTY_REQUIRES_FUNCTION, candidate.name
        )

    @read.register(ast.FunctionDef)
    @read.register(ast.AsyncFunctionDef)
    def read_function(
        self,
        statement: ast.FunctionDef | ast.AsyncFunctionDef,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
        member_kind: SourceMemberKind,
        placement: SourcePlacement,
    ) -> SourceClassProperty:
        return self.build(
            candidate=candidate,
            declaration_id=declaration_id,
            owner_declaration_id=owner_declaration_id,
            is_optional=statement.returns is not None and self.annotation_is_optional_dispatch(statement.returns),
            type=self.types.read(statement.returns),
            visibility=self.visibility.classify(candidate.name),
            member_kind=member_kind,
            placement=placement,
            assigned_value=self.assigned_values.unassigned(),
        )
