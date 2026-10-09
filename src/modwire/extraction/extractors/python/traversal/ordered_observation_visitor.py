import ast
from dataclasses import dataclass, field
from functools import singledispatchmethod

from ..observations.call_observation import PythonCallObservation
from ..observations.callable_candidate import PythonCallableCandidate
from ..observations.class_candidate import PythonClassCandidate
from ..observations.function_candidate import PythonFunctionCandidate
from ..observations.import_candidate import PythonImportCandidate
from ..observations.inheritance_candidate import PythonInheritanceCandidate
from ..observations.property_candidate import PythonPropertyCandidate
from ..observations.property_scope import PythonPropertyScope
from ..observations.source_observation import PythonSourceObservation
from ..observations.value_candidate import PythonValueCandidate
from .context import PythonTraversalContext
from .traversal_role import PythonTraversalRole


@dataclass
class OrderedObservationVisitor:
    positioned_classes: list[tuple[PythonClassCandidate, int, int]] = field(
        default_factory=list[tuple[PythonClassCandidate, int, int]]
    )
    functions: list[PythonFunctionCandidate] = field(default_factory=list[PythonFunctionCandidate])
    values: list[PythonValueCandidate] = field(default_factory=list[PythonValueCandidate])
    callables: list[PythonCallableCandidate] = field(default_factory=list[PythonCallableCandidate])
    positioned_lambdas: list[tuple[ast.Lambda, str, str, int, int, int]] = field(
        default_factory=list[tuple[ast.Lambda, str, str, int, int, int]]
    )
    positioned_imports: list[tuple[ast.Import | ast.ImportFrom, ast.alias, str, bool, int, int]] = field(
        default_factory=list[tuple[ast.Import | ast.ImportFrom, ast.alias, str, bool, int, int]]
    )
    lambda_names: dict[ast.Lambda, list[tuple[str, str]]] = field(
        default_factory=dict[ast.Lambda, list[tuple[str, str]]]
    )
    calls: dict[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, list[ast.Call]] = field(
        default_factory=dict[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, list[ast.Call]]
    )
    properties: list[PythonPropertyCandidate] = field(default_factory=list[PythonPropertyCandidate])
    lambdas_with_calls: set[ast.Lambda] = field(default_factory=set[ast.Lambda])
    node_counts_by_depth: dict[int, int] = field(default_factory=dict[int, int])
    stack: list[tuple[ast.AST, int, PythonTraversalContext, bool]] = field(
        default_factory=list[tuple[ast.AST, int, PythonTraversalContext, bool]]
    )
    sequence_at_depth: int = 0

    def read(self, tree: ast.Module) -> PythonSourceObservation:
        context = PythonTraversalContext(
            module=tree,
            parent_role=PythonTraversalRole.MODULE,
            class_name="",
            lambda_root="",
            lambda_owner="",
            lambda_root_ordinal=0,
            owners=(),
            property_contexts=(),
            direct_classes=(),
            active_lambda=tree,
        )
        self.node_counts_by_depth[0] = 1
        for child in reversed(tuple(ast.iter_child_nodes(tree))):
            self.stack.append((child, 1, context, False))
        visit = self.visit
        pop = self.stack.pop
        while self.stack:
            node, depth, context, completed = pop()
            if completed:
                self.finish_lambda(node, context)
                continue
            self.sequence_at_depth = self.node_counts_by_depth.get(depth, 0) + 1
            self.node_counts_by_depth[depth] = self.sequence_at_depth
            visit(node, depth, context)
        return self.observation()

    @singledispatchmethod
    def visit(self, node: ast.AST, depth: int, context: PythonTraversalContext) -> None:
        self.enqueue(node, depth, context)

    @visit.register
    def visit_ClassDef(self, node: ast.ClassDef, depth: int, context: PythonTraversalContext) -> None:
        self.positioned_classes.append(
            (
                PythonClassCandidate(
                    node=node,
                    ordinal=self.declaration_ordinal(node),
                    module_level=context.parent_role is PythonTraversalRole.MODULE,
                ),
                depth,
                self.sequence_at_depth,
            )
        )
        role = (
            PythonTraversalRole.MODULE_CLASS
            if context.parent_role is PythonTraversalRole.MODULE
            else PythonTraversalRole.NESTED_CLASS
        )
        body = set(node.body)
        body_context = PythonTraversalContext(
            module=context.module,
            parent_role=role,
            class_name=node.name,
            lambda_root=context.lambda_root,
            lambda_owner=context.lambda_owner,
            lambda_root_ordinal=context.lambda_root_ordinal,
            owners=(),
            property_contexts=context.property_contexts,
            direct_classes=((node.name, node.lineno, node.col_offset),),
            active_lambda=context.active_lambda,
        )
        nested_context = PythonTraversalContext(
            module=context.module,
            parent_role=PythonTraversalRole.NESTED,
            class_name=node.name,
            lambda_root=context.lambda_root,
            lambda_owner=context.lambda_owner,
            lambda_root_ordinal=context.lambda_root_ordinal,
            owners=(),
            property_contexts=context.property_contexts,
            direct_classes=(),
            active_lambda=context.active_lambda,
        )
        for child in reversed(tuple(ast.iter_child_nodes(node))):
            child_context = body_context if child in body else nested_context
            self.stack.append((child, depth + 1, child_context, False))

    @visit.register
    def visit_FunctionDef(self, node: ast.FunctionDef, depth: int, context: PythonTraversalContext) -> None:
        self.visit_function(node, depth, context)

    @visit.register
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef, depth: int, context: PythonTraversalContext) -> None:
        self.visit_function(node, depth, context)

    @visit.register
    def visit_Lambda(self, node: ast.Lambda, depth: int, context: PythonTraversalContext) -> None:
        if context.lambda_root:
            name = f"<anonymous>@{node.lineno}:{node.col_offset}"
            qualified_name = f"{context.lambda_root}.{name}"
            self.positioned_lambdas.append(
                (
                    node,
                    qualified_name,
                    context.lambda_owner,
                    context.lambda_root_ordinal,
                    depth,
                    self.sequence_at_depth,
                )
            )
            self.register_lambda(node, qualified_name, context.lambda_owner)
        owners: tuple[ast.Lambda, ...] = ()
        if node in self.lambda_names:
            owners = (node,)
        body_context = PythonTraversalContext(
            module=context.module,
            parent_role=PythonTraversalRole.NESTED,
            class_name=context.class_name,
            lambda_root=context.lambda_root,
            lambda_owner=context.lambda_owner,
            lambda_root_ordinal=context.lambda_root_ordinal,
            owners=owners,
            property_contexts=context.property_contexts,
            direct_classes=(),
            active_lambda=node,
        )
        nested_context = PythonTraversalContext(
            module=context.module,
            parent_role=PythonTraversalRole.NESTED,
            class_name=context.class_name,
            lambda_root=context.lambda_root,
            lambda_owner=context.lambda_owner,
            lambda_root_ordinal=context.lambda_root_ordinal,
            owners=(),
            property_contexts=context.property_contexts,
            direct_classes=(),
            active_lambda=node,
        )
        self.stack.append((node, depth, context, True))
        for child in reversed(tuple(ast.iter_child_nodes(node))):
            child_context = body_context if child is node.body else nested_context
            self.stack.append((child, depth + 1, child_context, False))

    @visit.register
    def visit_Call(self, node: ast.Call, depth: int, context: PythonTraversalContext) -> None:
        for owner in context.owners:
            if owner not in self.calls:
                self.calls[owner] = []
            self.calls[owner].append(node)
        self.mark_lambda_call(context.active_lambda)
        self.enqueue(node, depth, context)

    @visit.register
    def visit_Assign(self, node: ast.Assign, depth: int, context: PythonTraversalContext) -> None:
        if context.parent_role is PythonTraversalRole.MODULE:
            for target in node.targets:
                self.visit_assignment_target(target, node, node.value)
        for target in node.targets:
            self.collect_property_target(target, node, context)
        self.enqueue(node, depth, context)

    @visit.register
    def visit_AnnAssign(self, node: ast.AnnAssign, depth: int, context: PythonTraversalContext) -> None:
        if context.parent_role is PythonTraversalRole.MODULE:
            self.visit_annotated_target(node.target, node)
        self.collect_property_target(node.target, node, context)
        self.enqueue(node, depth, context)

    @visit.register
    def visit_Import(self, node: ast.Import, depth: int, context: PythonTraversalContext) -> None:
        self.positioned_imports.extend(
            (node, alias, alias.name, False, depth, self.sequence_at_depth) for alias in node.names
        )
        self.enqueue(node, depth, context)

    @visit.register
    def visit_ImportFrom(self, node: ast.ImportFrom, depth: int, context: PythonTraversalContext) -> None:
        path = f"{'.' * node.level}{node.module or ''}"
        self.positioned_imports.extend(
            (node, alias, path, node.level > 0, depth, self.sequence_at_depth) for alias in node.names
        )
        self.enqueue(node, depth, context)

    def visit_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, depth: int, context: PythonTraversalContext
    ) -> None:
        qualified_name = ""
        owner_name = ""
        if context.parent_role is PythonTraversalRole.MODULE:
            self.functions.append(PythonFunctionCandidate(node=node, ordinal=self.declaration_ordinal(node)))
            qualified_name = node.name
        elif context.parent_role in {PythonTraversalRole.MODULE_CLASS, PythonTraversalRole.NESTED_CLASS}:
            owner_name = context.class_name
            if context.parent_role is PythonTraversalRole.MODULE_CLASS:
                qualified_name = f"{owner_name}.{node.name}"
        lambda_root = context.lambda_root
        lambda_owner = context.lambda_owner
        lambda_root_ordinal = context.lambda_root_ordinal
        owners: tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...] = ()
        if qualified_name:
            ordinal = self.declaration_ordinal(node)
            self.callables.append(
                PythonCallableCandidate(
                    node=node,
                    identity_node=node,
                    name=node.name,
                    qualified_name=qualified_name,
                    owner_name=owner_name,
                    ordinal=ordinal,
                    requires_call=False,
                    root_ordinal=ordinal,
                    sequence=0,
                )
            )
            lambda_root = qualified_name
            lambda_owner = owner_name
            lambda_root_ordinal = ordinal
            owners = (node,)
        property_contexts = (
            *context.property_contexts,
            *(
                (class_name, class_line, class_column, node)
                for class_name, class_line, class_column in context.direct_classes
            ),
        )
        body = set(node.body)
        body_context = PythonTraversalContext(
            module=context.module,
            parent_role=PythonTraversalRole.NESTED,
            class_name=context.class_name,
            lambda_root=lambda_root,
            lambda_owner=lambda_owner,
            lambda_root_ordinal=lambda_root_ordinal,
            owners=owners,
            property_contexts=property_contexts,
            direct_classes=(),
            active_lambda=context.active_lambda,
        )
        nested_context = PythonTraversalContext(
            module=context.module,
            parent_role=PythonTraversalRole.NESTED,
            class_name=context.class_name,
            lambda_root=lambda_root,
            lambda_owner=lambda_owner,
            lambda_root_ordinal=lambda_root_ordinal,
            owners=(),
            property_contexts=property_contexts,
            direct_classes=(),
            active_lambda=context.active_lambda,
        )
        for child in reversed(tuple(ast.iter_child_nodes(node))):
            child_context = body_context if child in body else nested_context
            self.stack.append((child, depth + 1, child_context, False))

    def enqueue(self, node: ast.AST, depth: int, context: PythonTraversalContext) -> None:
        child_context = context
        if context.parent_role is not PythonTraversalRole.NESTED or context.direct_classes:
            child_context = PythonTraversalContext(
                module=context.module,
                parent_role=PythonTraversalRole.NESTED,
                class_name=context.class_name,
                lambda_root=context.lambda_root,
                lambda_owner=context.lambda_owner,
                lambda_root_ordinal=context.lambda_root_ordinal,
                owners=context.owners,
                property_contexts=context.property_contexts,
                direct_classes=(),
                active_lambda=context.active_lambda,
            )
        self.stack.extend(
            (child, depth + 1, child_context, False) for child in reversed(tuple(ast.iter_child_nodes(node)))
        )

    def observation(self) -> PythonSourceObservation:
        offsets = self.breadth_offsets()
        classes = tuple(
            item[0]
            for item in sorted(
                self.positioned_classes,
                key=lambda item: self.breadth_ordinal(item[1], item[2], offsets),
            )
        )
        self.callables.extend(
            PythonCallableCandidate(
                node=node,
                identity_node=node,
                name=qualified_name.rsplit(".", 1)[-1],
                qualified_name=qualified_name,
                owner_name=owner_name,
                ordinal=self.declaration_ordinal(node),
                requires_call=True,
                root_ordinal=root_ordinal,
                sequence=self.breadth_ordinal(depth, sequence, offsets),
            )
            for node, qualified_name, owner_name, root_ordinal, depth, sequence in self.positioned_lambdas
        )
        callables = tuple(
            sorted(
                (
                    candidate
                    for candidate in self.callables
                    if (not candidate.requires_call) or candidate.node in self.lambdas_with_calls
                ),
                key=lambda candidate: (candidate.root_ordinal, candidate.sequence),
            )
        )
        calls = tuple(
            PythonCallObservation(
                node=node,
                source_qualified_name=candidate.qualified_name,
                owner_name=candidate.owner_name,
            )
            for candidate in callables
            for node in (self.calls[candidate.node] if candidate.node in self.calls else ())
        )
        imports = tuple(
            PythonImportCandidate(
                node=node,
                alias=alias,
                path=path,
                is_relative=is_relative,
                statement_id=self.breadth_ordinal(depth, sequence, offsets),
            )
            for node, alias, path, is_relative, depth, sequence in sorted(
                self.positioned_imports,
                key=lambda item: self.breadth_ordinal(item[4], item[5], offsets),
            )
        )
        return PythonSourceObservation(
            classes=classes,
            functions=tuple(self.functions),
            values=tuple(self.values),
            callables=callables,
            calls=calls,
            imports=imports,
            exports=(),
            properties=tuple(self.properties),
            inheritance=tuple(
                PythonInheritanceCandidate(source=candidate, base=base)
                for candidate in classes
                for base in candidate.node.bases
            ),
        )

    def breadth_offsets(self) -> dict[int, int]:
        offsets: dict[int, int] = {}
        preceding = 0
        for depth in sorted(self.node_counts_by_depth):
            offsets[depth] = preceding
            preceding += self.node_counts_by_depth[depth]
        return offsets

    def breadth_ordinal(self, depth: int, sequence: int, offsets: dict[int, int]) -> int:
        return offsets[depth] + sequence

    @singledispatchmethod
    def visit_assignment_target(self, target: ast.expr, statement: ast.Assign, value: ast.expr) -> None:
        return

    @visit_assignment_target.register
    def visit_assignment_name(self, target: ast.Name, statement: ast.Assign, value: ast.expr) -> None:
        candidate = PythonValueCandidate(statement=statement, target=target, ordinal=self.declaration_ordinal(target))
        self.values.append(candidate)
        if target.id != "__all__":
            self.visit_assignment_value(value, candidate)

    @singledispatchmethod
    def visit_annotated_target(self, target: ast.expr, statement: ast.AnnAssign) -> None:
        return

    @visit_annotated_target.register
    def visit_annotated_name(self, target: ast.Name, statement: ast.AnnAssign) -> None:
        candidate = PythonValueCandidate(statement=statement, target=target, ordinal=self.declaration_ordinal(target))
        self.values.append(candidate)
        if statement.value is not None:
            self.visit_assignment_value(statement.value, candidate)

    @singledispatchmethod
    def visit_assignment_value(self, value: ast.expr, candidate: PythonValueCandidate) -> None:
        return

    @visit_assignment_value.register
    def visit_assignment_lambda(self, value: ast.Lambda, candidate: PythonValueCandidate) -> None:
        name = candidate.target.id
        self.callables.append(
            PythonCallableCandidate(
                node=value,
                identity_node=candidate.target,
                name=name,
                qualified_name=name,
                owner_name="",
                ordinal=candidate.ordinal,
                requires_call=False,
                root_ordinal=candidate.ordinal,
                sequence=0,
            )
        )
        self.register_lambda(value, name, "")

    def register_lambda(self, node: ast.Lambda, qualified_name: str, owner_name: str) -> None:
        if node not in self.lambda_names:
            self.lambda_names[node] = []
        self.lambda_names[node].append((qualified_name, owner_name))

    @singledispatchmethod
    def mark_lambda_call(self, node: ast.AST) -> None:
        return

    @mark_lambda_call.register
    def mark_lambda_with_call(self, node: ast.Lambda) -> None:
        self.lambdas_with_calls.add(node)

    @singledispatchmethod
    def finish_lambda(self, node: ast.AST, context: PythonTraversalContext) -> None:
        return

    @finish_lambda.register
    def finish_lambda_node(self, node: ast.Lambda, context: PythonTraversalContext) -> None:
        if node in self.lambdas_with_calls:
            self.mark_lambda_call(context.active_lambda)

    @singledispatchmethod
    def collect_property_target(
        self, target: ast.expr, statement: ast.Assign | ast.AnnAssign, context: PythonTraversalContext
    ) -> None:
        return

    @collect_property_target.register
    def collect_property_name(
        self, target: ast.Name, statement: ast.Assign | ast.AnnAssign, context: PythonTraversalContext
    ) -> None:
        for class_name, class_line, class_column in context.direct_classes:
            self.properties.append(
                PythonPropertyCandidate(
                    statement=statement,
                    class_name=class_name,
                    class_line=class_line,
                    class_column=class_column,
                    method=context.module,
                    name=target.id,
                    receiver="",
                    scope=PythonPropertyScope.CLASS,
                )
            )

    @collect_property_target.register
    def collect_property_attribute(
        self, target: ast.Attribute, statement: ast.Assign | ast.AnnAssign, context: PythonTraversalContext
    ) -> None:
        self.collect_property_receiver(target.value, target.attr, statement, context)

    @singledispatchmethod
    def collect_property_receiver(
        self,
        receiver: ast.expr,
        name: str,
        statement: ast.Assign | ast.AnnAssign,
        context: PythonTraversalContext,
    ) -> None:
        return

    @collect_property_receiver.register
    def collect_property_receiver_name(
        self,
        receiver: ast.Name,
        name: str,
        statement: ast.Assign | ast.AnnAssign,
        context: PythonTraversalContext,
    ) -> None:
        if receiver.id not in {"self", "cls"}:
            return
        for class_name, class_line, class_column, method in context.property_contexts:
            self.properties.append(
                PythonPropertyCandidate(
                    statement=statement,
                    class_name=class_name,
                    class_line=class_line,
                    class_column=class_column,
                    method=method,
                    name=name,
                    receiver=receiver.id,
                    scope=PythonPropertyScope.METHOD,
                )
            )

    @visit.register(ast.Constant)
    @visit.register(ast.alias)
    @visit.register(ast.operator)
    @visit.register(ast.unaryop)
    @visit.register(ast.boolop)
    @visit.register(ast.cmpop)
    @visit.register(ast.expr_context)
    @visit.register(ast.Pass)
    @visit.register(ast.Break)
    @visit.register(ast.Continue)
    @visit.register(ast.Global)
    @visit.register(ast.Nonlocal)
    @visit.register(ast.TypeIgnore)
    def visit_terminal(self, node: ast.AST, depth: int, context: PythonTraversalContext) -> None:
        return

    def declaration_ordinal(self, node: ast.stmt | ast.expr) -> int:
        return (node.lineno << 32) + node.col_offset + 1
