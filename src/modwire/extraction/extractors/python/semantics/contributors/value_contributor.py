import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ......shared.code.models.source_callable import SourceCallable
from ......shared.code.models.source_value import SourceValue
from ......shared.code.models.source_value_scope import SourceValueScope
from ......shared.code.models.types import SourceValueKind
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ...observations.value_candidate import PythonValueCandidate
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.assigned_value_reader import PythonAssignedValueReader
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..policies.type_alias_classifier import PythonTypeAliasClassifier
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="50-value")
@dataclass(frozen=True)
class ValueSemanticContributor(PythonSemanticContributor):
    aliases: PythonTypeAliasClassifier
    assigned_values: PythonAssignedValueReader
    visibility: PythonVisibilityPolicy
    identities: PythonDeclarationIdentityFactory

    @property
    def order(self) -> int:
        return 50

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        callables = {
            candidate.identity_node: source_callable
            for candidate, source_callable in zip(observation.callables, catalog.callables, strict=True)
        }
        values = tuple(
            self.source_value(candidate, callables, context)
            for candidate in observation.values
            if candidate.target.id != "__all__" and not self.aliases.is_alias(candidate)
        )
        return PythonSemanticContribution(values=values)

    def source_value(
        self,
        candidate: PythonValueCandidate,
        callables: dict[ast.stmt | ast.expr, SourceCallable],
        context: PythonSourceContext,
    ) -> SourceValue:
        declared_args = 0
        optional_args = 0
        if candidate.target in callables:
            source_callable = callables[candidate.target]
            declared_args = source_callable.declared_args
            optional_args = source_callable.optional_args
        line_end = candidate.statement.end_lineno
        if line_end is None:
            raise ValueError("Python value statement requires an end line.")
        return SourceValue(
            declaration_id=self.identities.create(
                context.source_id,
                DeclarationFamily.VALUE,
                candidate.target.id,
                candidate.target.lineno,
                candidate.target.col_offset,
            ),
            name=candidate.target.id,
            visibility="public",
            visibility_intent=self.visibility.classify(candidate.target.id),
            line_count=line_end - candidate.statement.lineno + 1,
            declaration_kind="constant" if self.is_constant(candidate) else "assignment",
            value_kind=self.value_kind(candidate.statement),
            scope=SourceValueScope.MODULE,
            declared_args=declared_args,
            optional_args=optional_args,
        )

    def is_constant(self, candidate: PythonValueCandidate) -> bool:
        return candidate.target.id.isupper() or self.has_final_annotation(candidate.statement)

    @singledispatchmethod
    def has_final_annotation(self, statement: ast.stmt) -> bool:
        return False

    @has_final_annotation.register
    def annotated_has_final_annotation(self, statement: ast.AnnAssign) -> bool:
        return ast.unparse(statement.annotation).rsplit(".", 1)[-1] == "Final"

    @singledispatchmethod
    def value_kind(self, statement: ast.stmt) -> SourceValueKind:
        return "unknown"

    @value_kind.register
    def assigned_value_kind(self, statement: ast.Assign) -> SourceValueKind:
        return self.expression_kind(statement.value)

    @value_kind.register
    def annotated_value_kind(self, statement: ast.AnnAssign) -> SourceValueKind:
        if statement.value is None:
            return "unknown"
        return self.expression_kind(statement.value)

    @singledispatchmethod
    def expression_kind(self, expression: ast.expr) -> SourceValueKind:
        return "unknown"

    @expression_kind.register
    def lambda_expression_kind(self, expression: ast.Lambda) -> SourceValueKind:
        return "callable"

    @expression_kind.register
    def constant_expression_kind(self, expression: ast.Constant) -> SourceValueKind:
        return "literal"

    @expression_kind.register
    def list_expression_kind(self, expression: ast.List) -> SourceValueKind:
        return "object"

    @expression_kind.register
    def tuple_expression_kind(self, expression: ast.Tuple) -> SourceValueKind:
        return "object"

    @expression_kind.register
    def set_expression_kind(self, expression: ast.Set) -> SourceValueKind:
        return "object"

    @expression_kind.register
    def dict_expression_kind(self, expression: ast.Dict) -> SourceValueKind:
        return "object"

    @expression_kind.register
    def call_expression_kind(self, expression: ast.Call) -> SourceValueKind:
        return "object"
