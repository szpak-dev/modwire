import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.source_declaration import SourceDeclaration
from ......shared.code.models.declarations.source_symbol_kind import SourceSymbolKind
from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ......shared.code.models.inventories.inventory_coverage import InventoryCoverage
from ......shared.code.models.inventories.inventory_status import InventoryStatus
from ......shared.code.models.inventories.member_inventory_coverage import MemberInventoryCoverage
from ......shared.code.models.values.source_value import SourceValue
from ......shared.code.models.values.source_value_declaration_kind import SourceValueDeclarationKind
from ......shared.code.models.values.source_value_scope import SourceValueScope
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ...observations.value_candidate import PythonValueCandidate
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="50-value")
@dataclass(frozen=True)
class ValueSemanticContributor(PythonSemanticContributor):
    visibility: PythonVisibilityPolicy

    @property
    def order(self) -> int:
        return 50

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        values: list[SourceValue] = []
        aliases: list[SourceDeclaration] = []
        for candidate in observation.values:
            if candidate.target not in catalog.scope_identities:
                continue
            if catalog.scope_identities[candidate.target].family is DeclarationFamily.TYPE:
                aliases.append(self.source_alias(candidate, catalog))
            else:
                values.append(self.source_value(candidate, catalog))
        return PythonSemanticContribution(values=tuple(values), declarations=tuple(aliases))

    def source_alias(self, candidate: PythonValueCandidate, catalog: PythonSemanticCatalog) -> SourceDeclaration:
        start, end = candidate.source_span
        absent = InventoryCoverage(status=InventoryStatus.NOT_APPLICABLE, limitations=())
        return SourceDeclaration(
            declaration_id=catalog.scope_identities[candidate.target],
            kind=SourceSymbolKind.TYPE_ALIAS,
            name=candidate.target.id,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.target.id),
            declaration_annotations=(),
            line_count=end - start + 1,
            placement=catalog.placement(candidate.binding_scope),
            inventory=MemberInventoryCoverage(
                methods=absent, abstract_methods=absent, properties=absent, signatures=absent
            ),
        )

    def source_value(
        self,
        candidate: PythonValueCandidate,
        catalog: PythonSemanticCatalog,
    ) -> SourceValue:
        start, end = candidate.source_span
        return SourceValue(
            declaration_id=catalog.scope_identities[candidate.target],
            name=candidate.target.id,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.target.id),
            line_count=end - start + 1,
            declaration_kind=(
                SourceValueDeclarationKind.CONSTANT
                if self.is_constant(candidate)
                else SourceValueDeclarationKind.ASSIGNMENT
            ),
            value_kind=self.value_kind(candidate.statement),
            scope=self.value_scope(candidate.binding_scope),
            placement=catalog.placement(candidate.binding_scope),
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

    @singledispatchmethod
    def value_scope(self, scope: ast.AST) -> SourceValueScope:
        return SourceValueScope.LOCAL

    @value_scope.register
    def module_value_scope(self, scope: ast.Module) -> SourceValueScope:
        return SourceValueScope.MODULE
