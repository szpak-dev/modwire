import ast
from dataclasses import dataclass, field
from functools import cached_property, singledispatchmethod

from .....shared.code.models.inventories.inventory_limitation import InventoryLimitation
from .....shared.code.models.inventories.inventory_limitation_kind import InventoryLimitationKind
from .....shared.code.models.inventories.inventory_source_location import InventorySourceLocation
from ...models.extractor_invariant_error import ExtractorInvariantError
from ...models.extractor_invariant_violation import ExtractorInvariantViolation
from ..observations.call_observation import PythonCallObservation
from ..observations.callable_candidate import PythonCallableCandidate
from ..observations.class_candidate import PythonClassCandidate
from ..observations.declaration_relation_candidate import PythonDeclarationRelationCandidate
from ..observations.import_candidate import PythonImportCandidate
from ..observations.inventory_evidence import PythonInventoryEvidence
from ..observations.property_candidate import PythonPropertyCandidate
from ..observations.source_observation import PythonSourceObservation
from ..observations.value_candidate import PythonValueCandidate
from .context import PythonTraversalContext
from .dispatch import PythonObservationDispatch


@dataclass
class OrderedObservationVisitor:
    classes: list[PythonClassCandidate] = field(default_factory=list[PythonClassCandidate])
    values: list[PythonValueCandidate] = field(default_factory=list[PythonValueCandidate])
    callables: list[PythonCallableCandidate] = field(default_factory=list[PythonCallableCandidate])
    calls: list[PythonCallObservation] = field(default_factory=list[PythonCallObservation])
    imports: list[PythonImportCandidate] = field(default_factory=list[PythonImportCandidate])
    properties: list[PythonPropertyCandidate] = field(default_factory=list[PythonPropertyCandidate])
    declaration_relations: list[PythonDeclarationRelationCandidate] = field(
        default_factory=list[PythonDeclarationRelationCandidate]
    )
    inventory: PythonInventoryEvidence = field(default_factory=PythonInventoryEvidence)
    lambda_bindings: dict[ast.Lambda, ast.Name] = field(default_factory=dict[ast.Lambda, ast.Name])
    call_ordinals: dict[ast.AST, int] = field(default_factory=dict[ast.AST, int])
    unresolved_bindings: dict[ast.AST, set[str]] = field(default_factory=dict[ast.AST, set[str]])

    @cached_property
    def dispatch(self) -> PythonObservationDispatch:
        return PythonObservationDispatch(
            visit=self.visit,
            observe_property_method=self.observe_property_method,
            observe_call=self.observe_call,
            bind_lambda=self.bind_lambda,
            bind_lambda_name=self.bind_lambda_name,
            observe_assignment=self.observe_assignment,
            observe_class_property=self.observe_class_property,
            observe_unresolved_binding=self.observe_unresolved_binding,
            observe_export_mutation=self.observe_export_mutation,
            limit_exports=self.limit_exports,
            limit_property_scope=self.limit_property_scope,
        )

    def read(self, tree: ast.Module) -> PythonSourceObservation:
        try:
            self.dispatch.visit(tree, 0, PythonTraversalContext(tree, ""))
        finally:
            del self.dispatch
        return PythonSourceObservation(
            classes=tuple(self.classes),
            values=tuple(self.values),
            callables=tuple(self.callables),
            calls=tuple(self.calls),
            imports=tuple(self.imports),
            exports=(),
            properties=tuple(self.properties),
            declaration_relations=tuple(self.declaration_relations),
            inventory=self.inventory,
            unresolved_bindings=self.unresolved_bindings,
        )

    def qualified_name(self, context: PythonTraversalContext, name: str) -> str:
        return f"{context.qualified_name}.{name}" if context.qualified_name else name

    def source_span(self, node: ast.stmt | ast.expr) -> tuple[int, int]:
        if node.end_lineno is None:
            raise ExtractorInvariantError(ExtractorInvariantViolation.MISSING_SOURCE_END_LINE, ast.unparse(node))
        return (node.lineno, node.end_lineno)

    def declaration_ordinal(self, node: ast.stmt | ast.expr) -> int:
        return (node.lineno << 32) + node.col_offset + 1

    @singledispatchmethod
    def visit(self, node: ast.AST, depth: int, context: PythonTraversalContext) -> None:
        for child in ast.iter_child_nodes(node):
            self.dispatch.visit(child, depth + 1, context)

    @visit.register
    def visit_ClassDef(self, node: ast.ClassDef, depth: int, context: PythonTraversalContext) -> None:
        candidate = PythonClassCandidate(
            node,
            context.binding_scope,
            self.qualified_name(context, node.name),
            self.declaration_ordinal(node),
            self.source_span(node),
        )
        self.classes.append(candidate)
        self.inventory.methods[node] = []
        self.inventory.properties[node] = []
        self.declaration_relations.extend(PythonDeclarationRelationCandidate(candidate, base) for base in node.bases)
        for expression in (*node.decorator_list, *node.bases, *(keyword.value for keyword in node.keywords)):
            self.dispatch.visit(expression, depth + 1, context)
        nested = PythonTraversalContext(node, candidate.qualified_name)
        for statement in node.body:
            self.dispatch.visit(statement, depth + 1, nested)

    @visit.register(ast.FunctionDef)
    @visit.register(ast.AsyncFunctionDef)
    def visit_FunctionDef(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, depth: int, context: PythonTraversalContext
    ) -> None:
        ordinal = self.declaration_ordinal(node)
        candidate = PythonCallableCandidate(
            node,
            node,
            context.binding_scope,
            node.name,
            self.qualified_name(context, node.name),
            ordinal,
            ordinal,
            0,
            self.source_span(node),
        )
        self.callables.append(candidate)
        self.dispatch.observe_property_method(context.binding_scope, node, candidate.source_span, ordinal)
        for expression in (*node.decorator_list, *node.args.defaults):
            self.dispatch.visit(expression, depth + 1, context)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.dispatch.visit(expression, depth + 1, context)
        nested = PythonTraversalContext(node, candidate.qualified_name)
        for statement in node.body:
            self.dispatch.visit(statement, depth + 1, nested)

    @singledispatchmethod
    def observe_property_method(
        self, scope: ast.AST, node: ast.FunctionDef | ast.AsyncFunctionDef, span: tuple[int, int], ordinal: int
    ) -> None:
        return

    @observe_property_method.register
    def class_property_method(
        self, scope: ast.ClassDef, node: ast.FunctionDef | ast.AsyncFunctionDef, span: tuple[int, int], ordinal: int
    ) -> None:
        if any(ast.unparse(decorator).rsplit(".", 1)[-1] == "property" for decorator in node.decorator_list):
            self.properties.append(PythonPropertyCandidate(node, scope, node.name, span, ordinal, node))

    @visit.register
    def visit_Lambda(self, node: ast.Lambda, depth: int, context: PythonTraversalContext) -> None:
        identity_node: ast.expr = node
        name = f"<lambda@{node.lineno}:{node.col_offset}>"
        if node in self.lambda_bindings:
            identity_node = self.lambda_bindings[node]
            name = self.lambda_bindings[node].id
        ordinal = self.declaration_ordinal(identity_node)
        candidate = PythonCallableCandidate(
            node,
            identity_node,
            context.binding_scope,
            name,
            self.qualified_name(context, name),
            ordinal,
            ordinal,
            0,
            self.source_span(node),
        )
        self.callables.append(candidate)
        for expression in node.args.defaults:
            self.dispatch.visit(expression, depth + 1, context)
        for expression in node.args.kw_defaults:
            if expression is not None:
                self.dispatch.visit(expression, depth + 1, context)
        self.dispatch.visit(node.body, depth + 1, PythonTraversalContext(node, candidate.qualified_name))

    @visit.register
    def visit_Call(self, node: ast.Call, depth: int, context: PythonTraversalContext) -> None:
        self.dispatch.observe_export_mutation(node.func, node, context)
        self.dispatch.observe_call(context.binding_scope, node)
        for child in ast.iter_child_nodes(node):
            self.dispatch.visit(child, depth + 1, context)

    @singledispatchmethod
    def observe_call(self, scope: ast.AST, node: ast.Call) -> None:
        return

    @observe_call.register(ast.FunctionDef)
    @observe_call.register(ast.AsyncFunctionDef)
    @observe_call.register(ast.Lambda)
    def callable_call(self, scope: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, node: ast.Call) -> None:
        ordinal = self.call_ordinals[scope] + 1 if scope in self.call_ordinals else 1
        self.call_ordinals[scope] = ordinal
        self.calls.append(PythonCallObservation(node, ordinal, scope, scope))

    @visit.register
    def visit_Assign(self, node: ast.Assign, depth: int, context: PythonTraversalContext) -> None:
        for target in node.targets:
            self.dispatch.observe_assignment(target, node, context)
        if len(node.targets) == 1:
            self.dispatch.bind_lambda(node.value, node.targets[0])
        self.dispatch.visit(node.value, depth + 1, context)

    @visit.register
    def visit_AnnAssign(self, node: ast.AnnAssign, depth: int, context: PythonTraversalContext) -> None:
        self.dispatch.observe_assignment(node.target, node, context)
        if node.value is not None:
            self.dispatch.bind_lambda(node.value, node.target)
            self.dispatch.visit(node.value, depth + 1, context)

    @singledispatchmethod
    def bind_lambda(self, value: ast.expr, target: ast.expr) -> None:
        return

    @bind_lambda.register
    def lambda_binding(self, value: ast.Lambda, target: ast.expr) -> None:
        self.dispatch.bind_lambda_name(target, value)

    @singledispatchmethod
    def bind_lambda_name(self, target: ast.expr, value: ast.Lambda) -> None:
        return

    @bind_lambda_name.register
    def lambda_name_binding(self, target: ast.Name, value: ast.Lambda) -> None:
        self.lambda_bindings[value] = target

    @singledispatchmethod
    def observe_assignment(
        self, target: ast.expr, statement: ast.Assign | ast.AnnAssign, context: PythonTraversalContext
    ) -> None:
        self.dispatch.observe_export_mutation(target, statement, context)
        self.dispatch.visit(target, 0, context)
        limitation = self.inventory_limitation(
            statement,
            InventoryLimitationKind.UNSUPPORTED_SYNTAX,
            "Assignment target is outside the represented value inventory.",
        )
        self.inventory.values.append(limitation)
        self.inventory.callable_values.append(limitation)
        self.dispatch.limit_property_scope(context.binding_scope, limitation)

    @observe_assignment.register
    def name_assignment(
        self, target: ast.Name, statement: ast.Assign | ast.AnnAssign, context: PythonTraversalContext
    ) -> None:
        candidate = PythonValueCandidate(
            statement,
            target,
            context.binding_scope,
            self.qualified_name(context, target.id),
            self.declaration_ordinal(target),
            self.source_span(statement),
        )
        self.values.append(candidate)
        self.dispatch.observe_class_property(context.binding_scope, statement, candidate)

    @singledispatchmethod
    def observe_class_property(
        self, scope: ast.AST, statement: ast.Assign | ast.AnnAssign, candidate: PythonValueCandidate
    ) -> None:
        return

    @observe_class_property.register
    def class_assignment(
        self,
        scope: ast.ClassDef,
        statement: ast.Assign | ast.AnnAssign,
        candidate: PythonValueCandidate,
    ) -> None:
        self.properties.append(
            PythonPropertyCandidate(
                statement, scope, candidate.target.id, candidate.source_span, candidate.ordinal, candidate.target
            )
        )

    @observe_assignment.register
    def attribute_assignment(
        self, target: ast.Attribute, statement: ast.Assign | ast.AnnAssign, context: PythonTraversalContext
    ) -> None:
        self.properties.append(
            PythonPropertyCandidate(
                statement,
                context.binding_scope,
                target.attr,
                self.source_span(statement),
                self.declaration_ordinal(target),
                target,
            )
        )

    @visit.register
    def visit_Import(self, node: ast.Import, depth: int, context: PythonTraversalContext) -> None:
        self.imports.extend(
            PythonImportCandidate(node, context.binding_scope, alias, alias.name, False, self.declaration_ordinal(node))
            for alias in node.names
        )

    @visit.register
    def visit_ImportFrom(self, node: ast.ImportFrom, depth: int, context: PythonTraversalContext) -> None:
        path = f"{'.' * node.level}{node.module or ''}"
        self.imports.extend(
            PythonImportCandidate(
                node, context.binding_scope, alias, path, node.level > 0, self.declaration_ordinal(node)
            )
            for alias in node.names
        )
        if any(alias.name == "*" for alias in node.names):
            self.inventory.implicit_exports.append(
                self.inventory_limitation(
                    node,
                    InventoryLimitationKind.DYNAMIC_STRUCTURE,
                    "Wildcard import bindings require imported-module execution.",
                )
            )

    def inventory_limitation(
        self, node: ast.stmt | ast.expr, kind: InventoryLimitationKind, description: str
    ) -> InventoryLimitation:
        start, end = self.source_span(node)
        return InventoryLimitation(
            kind=kind, location=InventorySourceLocation(start_line=start, end_line=end), description=description
        )

    @visit.register
    def visit_TypeAlias(self, node: ast.TypeAlias, depth: int, context: PythonTraversalContext) -> None:
        self.values.append(
            PythonValueCandidate(
                node,
                node.name,
                context.binding_scope,
                self.qualified_name(context, node.name.id),
                self.declaration_ordinal(node.name),
                self.source_span(node),
            )
        )
        self.dispatch.visit(node.value, depth + 1, context)

    @visit.register
    def visit_exception_handler(self, node: ast.ExceptHandler, depth: int, context: PythonTraversalContext) -> None:
        if node.name is not None:
            self.record_unresolved_binding(node.name, context)
            limitation = InventoryLimitation(
                kind=InventoryLimitationKind.UNSUPPORTED_SYNTAX,
                location=InventorySourceLocation(start_line=node.lineno, end_line=node.lineno),
                description="Exception target binding is outside the represented value inventory.",
            )
            self.inventory.values.append(limitation)
            self.dispatch.limit_property_scope(context.binding_scope, limitation)
        for child in ast.iter_child_nodes(node):
            self.dispatch.visit(child, depth + 1, context)

    @visit.register(ast.For)
    @visit.register(ast.AsyncFor)
    @visit.register(ast.With)
    @visit.register(ast.AsyncWith)
    @visit.register(ast.NamedExpr)
    @visit.register(ast.AugAssign)
    @visit.register(ast.Match)
    @visit.register(ast.ListComp)
    @visit.register(ast.SetComp)
    @visit.register(ast.DictComp)
    @visit.register(ast.GeneratorExp)
    def visit_binding_statement(
        self,
        node: ast.For
        | ast.AsyncFor
        | ast.With
        | ast.AsyncWith
        | ast.NamedExpr
        | ast.AugAssign
        | ast.Match
        | ast.ListComp
        | ast.SetComp
        | ast.DictComp
        | ast.GeneratorExp,
        depth: int,
        context: PythonTraversalContext,
    ) -> None:
        limitation = self.inventory_limitation(
            node,
            InventoryLimitationKind.UNSUPPORTED_SYNTAX,
            "Binding form is outside the represented assignment inventory.",
        )
        self.inventory.values.append(limitation)
        self.inventory.callable_values.append(limitation)
        self.dispatch.limit_property_scope(context.binding_scope, limitation)
        self.dispatch.observe_export_mutation(node, node, context)
        for child in ast.iter_child_nodes(node):
            self.dispatch.visit(child, depth + 1, context)

    @visit.register
    def visit_Delete(self, node: ast.Delete, depth: int, context: PythonTraversalContext) -> None:
        for target in node.targets:
            self.dispatch.observe_export_mutation(target, node, context)
            self.dispatch.visit(target, depth + 1, context)

    @visit.register
    def visit_Name(self, node: ast.Name, depth: int, context: PythonTraversalContext) -> None:
        self.dispatch.observe_unresolved_binding(node.ctx, node.id, context)

    @singledispatchmethod
    def observe_unresolved_binding(
        self, operation: ast.expr_context, name: str, context: PythonTraversalContext
    ) -> None:
        return

    @observe_unresolved_binding.register(ast.Store)
    @observe_unresolved_binding.register(ast.Del)
    def unresolved_name_binding(
        self, operation: ast.Store | ast.Del, name: str, context: PythonTraversalContext
    ) -> None:
        self.record_unresolved_binding(name, context)

    def record_unresolved_binding(self, name: str, context: PythonTraversalContext) -> None:
        if context.binding_scope not in self.unresolved_bindings:
            self.unresolved_bindings[context.binding_scope] = set()
        self.unresolved_bindings[context.binding_scope].add(name)

    @visit.register(ast.Global)
    @visit.register(ast.Nonlocal)
    def visit_scope_directive(
        self, node: ast.Global | ast.Nonlocal, depth: int, context: PythonTraversalContext
    ) -> None:
        for name in node.names:
            self.record_unresolved_binding(name, context)

    @visit.register(ast.MatchAs)
    @visit.register(ast.MatchStar)
    def visit_pattern_binding(
        self, node: ast.MatchAs | ast.MatchStar, depth: int, context: PythonTraversalContext
    ) -> None:
        if node.name is not None:
            self.record_unresolved_binding(node.name, context)
        for child in ast.iter_child_nodes(node):
            self.dispatch.visit(child, depth + 1, context)

    @visit.register
    def visit_mapping_binding(self, node: ast.MatchMapping, depth: int, context: PythonTraversalContext) -> None:
        if node.rest is not None:
            self.record_unresolved_binding(node.rest, context)
        for child in ast.iter_child_nodes(node):
            self.dispatch.visit(child, depth + 1, context)

    @singledispatchmethod
    def observe_export_mutation(
        self, target: ast.AST, node: ast.stmt | ast.expr, context: PythonTraversalContext
    ) -> None:
        return

    @observe_export_mutation.register
    def augmented_export_mutation(
        self, target: ast.AugAssign, node: ast.stmt | ast.expr, context: PythonTraversalContext
    ) -> None:
        self.dispatch.observe_export_mutation(target.target, node, context)

    @observe_export_mutation.register(ast.Attribute)
    @observe_export_mutation.register(ast.Subscript)
    def attribute_export_mutation(
        self, target: ast.Attribute | ast.Subscript, node: ast.stmt | ast.expr, context: PythonTraversalContext
    ) -> None:
        self.dispatch.observe_export_mutation(target.value, node, context)

    @observe_export_mutation.register
    def named_export_mutation(
        self, target: ast.Name, node: ast.stmt | ast.expr, context: PythonTraversalContext
    ) -> None:
        if target.id == "__all__":
            self.dispatch.limit_exports(context.binding_scope, node)

    @singledispatchmethod
    def limit_exports(self, scope: ast.AST, node: ast.stmt | ast.expr) -> None:
        return

    @limit_exports.register
    def limit_module_exports(self, scope: ast.Module, node: ast.stmt | ast.expr) -> None:
        self.inventory.exports.append(
            self.inventory_limitation(
                node,
                InventoryLimitationKind.DYNAMIC_STRUCTURE,
                "Explicit export bindings are mutated outside a literal assignment.",
            )
        )

    @singledispatchmethod
    def limit_property_scope(self, scope: ast.AST, limitation: InventoryLimitation) -> None:
        return

    @limit_property_scope.register
    def limit_class_properties(self, scope: ast.ClassDef, limitation: InventoryLimitation) -> None:
        self.inventory.properties[scope].append(limitation)
