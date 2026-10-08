import ast
from dataclasses import dataclass, field
from functools import singledispatchmethod

from ..observations.property_candidate import PythonPropertyCandidate
from ..observations.source_observation import PythonSourceObservation


@dataclass
class DepthFirstObservationVisitor:
    callable_names: dict[ast.FunctionDef | ast.AsyncFunctionDef, tuple[str, str]]
    lambda_names: dict[ast.Lambda, list[tuple[str, str]]]
    calls: dict[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, list[ast.Call]] = field(
        default_factory=dict[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, list[ast.Call]]
    )
    properties: list[PythonPropertyCandidate] = field(default_factory=list[PythonPropertyCandidate])
    lambdas_with_calls: set[ast.Lambda] = field(default_factory=set[ast.Lambda])
    stack: list[
        tuple[
            ast.AST,
            tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, ...],
            tuple[tuple[str, int, int, ast.FunctionDef | ast.AsyncFunctionDef], ...],
            tuple[tuple[str, int, int], ...],
            ast.Module | ast.Lambda,
            bool,
        ]
    ] = field(
        default_factory=list[
            tuple[
                ast.AST,
                tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, ...],
                tuple[tuple[str, int, int, ast.FunctionDef | ast.AsyncFunctionDef], ...],
                tuple[tuple[str, int, int], ...],
                ast.Module | ast.Lambda,
                bool,
            ]
        ]
    )
    owners: tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, ...] = ()
    property_contexts: tuple[tuple[str, int, int, ast.FunctionDef | ast.AsyncFunctionDef], ...] = ()
    direct_classes: tuple[tuple[str, int, int], ...] = ()
    active_lambda: ast.Module | ast.Lambda = field(default_factory=lambda: ast.Module(body=[], type_ignores=[]))
    module: ast.Module = field(default_factory=lambda: ast.Module(body=[], type_ignores=[]))

    def read(self, tree: ast.Module) -> PythonSourceObservation:
        self.module = tree
        self.enqueue(tree, (), (), self.module)
        while self.stack:
            (
                node,
                self.owners,
                self.property_contexts,
                self.direct_classes,
                self.active_lambda,
                completed,
            ) = self.stack.pop()
            if completed:
                self.finish_lambda(node)
                continue
            self.visit(node)
        return PythonSourceObservation(
            classes=(),
            functions=(),
            values=(),
            callables=(),
            calls=(),
            imports=(),
            exports=(),
            properties=tuple(self.properties),
            inheritance=(),
        )

    @singledispatchmethod
    def visit(self, node: ast.AST) -> None:
        self.enqueue(node, self.owners, self.property_contexts, self.active_lambda)

    @visit.register
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        body = set(node.body)
        for child in reversed(tuple(ast.iter_child_nodes(node))):
            direct_classes: tuple[tuple[str, int, int], ...] = ()
            if child in body:
                direct_classes = ((node.name, node.lineno, node.col_offset),)
            self.stack.append((child, (), self.property_contexts, direct_classes, self.active_lambda, False))

    @visit.register
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.visit_function(node)

    @visit.register
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_function(node)

    @visit.register
    def visit_Lambda(self, node: ast.Lambda) -> None:
        owners: tuple[ast.Lambda, ...] = ()
        if node in self.lambda_names:
            owners = (node,)
        self.stack.append((node, self.owners, self.property_contexts, self.direct_classes, self.active_lambda, True))
        for child in reversed(tuple(ast.iter_child_nodes(node))):
            child_owners = owners if child is node.body else ()
            self.stack.append((child, child_owners, self.property_contexts, (), node, False))

    @visit.register
    def visit_Call(self, node: ast.Call) -> None:
        for owner in self.owners:
            if owner not in self.calls:
                self.calls[owner] = []
            self.calls[owner].append(node)
        self.mark_lambda_call(self.active_lambda)
        self.enqueue(node, self.owners, self.property_contexts, self.active_lambda)

    @visit.register
    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self.collect_property_target(target, node)
        self.enqueue(node, self.owners, self.property_contexts, self.active_lambda)

    @visit.register
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.collect_property_target(node.target, node)
        self.enqueue(node, self.owners, self.property_contexts, self.active_lambda)

    def visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        owners: tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...] = ()
        if node in self.callable_names:
            owners = (node,)
        property_contexts = (
            *self.property_contexts,
            *(
                (class_name, class_line, class_column, node)
                for class_name, class_line, class_column in self.direct_classes
            ),
        )
        body = set(node.body)
        for child in reversed(tuple(ast.iter_child_nodes(node))):
            child_owners = owners if child in body else ()
            self.stack.append((child, child_owners, property_contexts, (), self.active_lambda, False))

    def enqueue(
        self,
        node: ast.AST,
        owners: tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda, ...],
        property_contexts: tuple[tuple[str, int, int, ast.FunctionDef | ast.AsyncFunctionDef], ...],
        active_lambda: ast.Module | ast.Lambda,
    ) -> None:
        self.stack.extend(
            (child, owners, property_contexts, (), active_lambda, False)
            for child in reversed(tuple(ast.iter_child_nodes(node)))
        )

    @singledispatchmethod
    def mark_lambda_call(self, node: ast.AST) -> None:
        return

    @mark_lambda_call.register
    def mark_lambda_with_call(self, node: ast.Lambda) -> None:
        self.lambdas_with_calls.add(node)

    @singledispatchmethod
    def finish_lambda(self, node: ast.AST) -> None:
        return

    @finish_lambda.register
    def finish_lambda_node(self, node: ast.Lambda) -> None:
        if node in self.lambdas_with_calls:
            self.mark_lambda_call(self.active_lambda)

    @singledispatchmethod
    def collect_property_target(self, target: ast.expr, statement: ast.Assign | ast.AnnAssign) -> None:
        return

    @collect_property_target.register
    def collect_property_name(self, target: ast.Name, statement: ast.Assign | ast.AnnAssign) -> None:
        for class_name, class_line, class_column in self.direct_classes:
            self.properties.append(
                PythonPropertyCandidate(
                    statement=statement,
                    class_name=class_name,
                    class_line=class_line,
                    class_column=class_column,
                    method=self.module,
                    name=target.id,
                    receiver="",
                    scope="class",
                )
            )

    def collect_method_property(
        self,
        class_name: str,
        class_line: int,
        class_column: int,
        method: ast.FunctionDef | ast.AsyncFunctionDef,
        receiver: ast.Name,
        name: str,
        statement: ast.Assign | ast.AnnAssign,
    ) -> None:
        if receiver.id not in {"self", "cls"}:
            return
        self.properties.append(
            PythonPropertyCandidate(
                statement=statement,
                class_name=class_name,
                class_line=class_line,
                class_column=class_column,
                method=method,
                name=name,
                receiver=receiver.id,
                scope="method",
            )
        )

    @collect_property_target.register
    def collect_property_attribute(self, target: ast.Attribute, statement: ast.Assign | ast.AnnAssign) -> None:
        self.collect_property_receiver(target.value, target.attr, statement)

    @singledispatchmethod
    def collect_property_receiver(self, receiver: ast.expr, name: str, statement: ast.Assign | ast.AnnAssign) -> None:
        return

    @collect_property_receiver.register
    def collect_property_receiver_name(
        self, receiver: ast.Name, name: str, statement: ast.Assign | ast.AnnAssign
    ) -> None:
        for class_name, class_line, class_column, method in self.property_contexts:
            self.collect_method_property(
                class_name,
                class_line,
                class_column,
                method,
                receiver,
                name,
                statement,
            )
