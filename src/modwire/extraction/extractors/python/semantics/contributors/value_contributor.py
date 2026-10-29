import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ......shared.code.models.source_symbol_kind import SourceSymbolKind
from ......shared.code.models.values.source_value import SourceValue
from ......shared.code.models.values.source_value_declaration_kind import SourceValueDeclarationKind
from ......shared.code.models.values.source_value_scope import SourceValueScope
from ....models.extractor_invariant_error import ExtractorInvariantError
from ....models.extractor_invariant_violation import ExtractorInvariantViolation
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
        values = tuple(
            self.source_value(candidate, context)
            for candidate in observation.values
            if candidate.target.id != "__all__"
            and not self.aliases.is_alias(candidate)
            and self.value_kind(candidate.statement) is not SourceSymbolKind.VALUE_CALLABLE
        )
        return PythonSemanticContribution(values=values)

    def source_value(
        self,
        candidate: PythonValueCandidate,
        context: PythonSourceContext,
    ) -> SourceValue:
        line_end = candidate.statement.end_lineno
        if line_end is None:
            raise ExtractorInvariantError(ExtractorInvariantViolation.MISSING_VALUE_END_LINE, candidate.target.id)
        return SourceValue(
            declaration_id=self.identities.create(
                context.source_id,
                DeclarationFamily.VALUE,
                candidate.target.id,
                candidate.target.lineno,
                candidate.target.col_offset,
            ),
            name=candidate.target.id,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.target.id),
            line_count=line_end - candidate.statement.lineno + 1,
            declaration_kind=(
                SourceValueDeclarationKind.CONSTANT
                if self.is_constant(candidate)
                else SourceValueDeclarationKind.ASSIGNMENT
            ),
            value_kind=self.value_kind(candidate.statement),
            scope=SourceValueScope.MODULE,
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
    def value_kind(self, statement: ast.stmt) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_UNKNOWN

    @value_kind.register
    def assigned_value_kind(self, statement: ast.Assign) -> SourceSymbolKind:
        return self.expression_kind(statement.value)

    @value_kind.register
    def annotated_value_kind(self, statement: ast.AnnAssign) -> SourceSymbolKind:
        if statement.value is None:
            return SourceSymbolKind.VALUE_UNKNOWN
        return self.expression_kind(statement.value)

    @singledispatchmethod
    def expression_kind(self, expression: ast.expr) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_UNKNOWN

    @expression_kind.register
    def lambda_expression_kind(self, expression: ast.Lambda) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_CALLABLE

    @expression_kind.register
    def constant_expression_kind(self, expression: ast.Constant) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_LITERAL

    @expression_kind.register
    def list_expression_kind(self, expression: ast.List) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_OBJECT

    @expression_kind.register
    def tuple_expression_kind(self, expression: ast.Tuple) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_OBJECT

    @expression_kind.register
    def set_expression_kind(self, expression: ast.Set) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_OBJECT

    @expression_kind.register
    def dict_expression_kind(self, expression: ast.Dict) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_OBJECT

    @expression_kind.register
    def call_expression_kind(self, expression: ast.Call) -> SourceSymbolKind:
        return SourceSymbolKind.VALUE_OBJECT
