import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_member_kind import SourceMemberKind
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
from ...observations.property_candidate import PythonPropertyCandidate
from ...observations.property_scope import PythonPropertyScope
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

    @property
    def order(self) -> int:
        return 50

    def applies(self, candidate: PythonPropertyCandidate) -> bool:
        return candidate.scope is PythonPropertyScope.METHOD and self.has_property_decorator(candidate.statement)

    def classify(
        self,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        return self.read(candidate.statement, candidate, declaration_id, owner_declaration_id)

    @singledispatchmethod
    def has_property_decorator(self, statement: ast.stmt) -> bool:
        return False

    @has_property_decorator.register
    def function_has_property_decorator(self, statement: ast.FunctionDef) -> bool:
        return any(ast.unparse(item).rsplit(".", 1)[-1] == "property" for item in statement.decorator_list)

    @has_property_decorator.register
    def async_function_has_property_decorator(self, statement: ast.AsyncFunctionDef) -> bool:
        return any(ast.unparse(item).rsplit(".", 1)[-1] == "property" for item in statement.decorator_list)

    @singledispatchmethod
    def read(
        self,
        statement: ast.stmt,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        raise ExtractorInvariantError(
            ExtractorInvariantViolation.DECORATED_METHOD_PROPERTY_REQUIRES_FUNCTION, candidate.name
        )

    @read.register
    def read_function(
        self,
        statement: ast.FunctionDef,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        return self.build_method(statement, candidate, declaration_id, owner_declaration_id)

    @read.register
    def read_async_function(
        self,
        statement: ast.AsyncFunctionDef,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        return self.build_method(statement, candidate, declaration_id, owner_declaration_id)

    def build_method(
        self,
        statement: ast.FunctionDef | ast.AsyncFunctionDef,
        candidate: PythonPropertyCandidate,
        declaration_id: DeclarationIdentity,
        owner_declaration_id: DeclarationIdentity,
    ) -> SourceClassProperty:
        return self.build(
            candidate=candidate,
            declaration_id=declaration_id,
            owner_declaration_id=owner_declaration_id,
            is_optional=statement.returns is not None and self.annotation_is_optional(statement.returns),
            type=self.types.read(statement.returns),
            visibility=self.visibility.classify(candidate.name),
            member_kind=SourceMemberKind.INSTANCE,
            assigned_value=self.assigned_values.unassigned(),
        )
