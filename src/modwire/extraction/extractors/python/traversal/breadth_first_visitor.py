import ast
from collections import deque
from dataclasses import dataclass, field
from functools import singledispatchmethod

from ..observations.callable_candidate import PythonCallableCandidate
from ..observations.class_candidate import PythonClassCandidate
from ..observations.function_candidate import PythonFunctionCandidate
from ..observations.import_candidate import PythonImportCandidate
from ..observations.inheritance_candidate import PythonInheritanceCandidate
from ..observations.source_observation import PythonSourceObservation
from ..observations.value_candidate import PythonValueCandidate


@dataclass
class BreadthFirstObservationVisitor:
    classes: list[PythonClassCandidate] = field(default_factory=list[PythonClassCandidate])
    functions: list[PythonFunctionCandidate] = field(default_factory=list[PythonFunctionCandidate])
    values: list[PythonValueCandidate] = field(default_factory=list[PythonValueCandidate])
    callables: list[PythonCallableCandidate] = field(default_factory=list[PythonCallableCandidate])
    imports: list[PythonImportCandidate] = field(default_factory=list[PythonImportCandidate])
    callable_names: dict[ast.FunctionDef | ast.AsyncFunctionDef, tuple[str, str]] = field(
        default_factory=dict[ast.FunctionDef | ast.AsyncFunctionDef, tuple[str, str]]
    )
    lambda_names: dict[ast.Lambda, list[tuple[str, str]]] = field(
        default_factory=dict[ast.Lambda, list[tuple[str, str]]]
    )
    queue: deque[tuple[ast.AST, str, str, str, str, int]] = field(
        default_factory=deque[tuple[ast.AST, str, str, str, str, int]]
    )
    parent_role: str = "nested"
    class_name: str = ""
    lambda_root: str = ""
    lambda_owner: str = ""
    lambda_root_ordinal: int = 0
    statement_id: int = 0

    def read(self, tree: ast.Module) -> PythonSourceObservation:
        self.statement_id = 1
        self.enqueue(tree, "module", "", "", "", 0)
        while self.queue:
            (
                node,
                self.parent_role,
                self.class_name,
                self.lambda_root,
                self.lambda_owner,
                self.lambda_root_ordinal,
            ) = self.queue.popleft()
            self.statement_id += 1
            self.visit(node, self.statement_id)
        return PythonSourceObservation(
            classes=tuple(self.classes),
            functions=tuple(self.functions),
            values=tuple(self.values),
            callables=tuple(self.callables),
            calls=(),
            imports=tuple(self.imports),
            exports=(),
            properties=(),
            inheritance=self.inheritance_candidates(),
        )

    @singledispatchmethod
    def visit(self, node: ast.AST, ordinal: int) -> None:
        self.enqueue(
            node,
            "nested",
            self.class_name,
            self.lambda_root,
            self.lambda_owner,
            self.lambda_root_ordinal,
        )

    @visit.register
    def visit_ClassDef(self, node: ast.ClassDef, ordinal: int) -> None:
        candidate = PythonClassCandidate(
            node=node,
            ordinal=self.declaration_ordinal(node),
            module_level=self.parent_role == "module",
        )
        self.classes.append(candidate)
        if self.parent_role == "module":
            self.enqueue_class(node, "module_class", node.name)
            return
        self.enqueue_class(node, "nested_class", node.name)

    @visit.register
    def visit_FunctionDef(self, node: ast.FunctionDef, ordinal: int) -> None:
        self.visit_function(node, ordinal)

    @visit.register
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef, ordinal: int) -> None:
        self.visit_function(node, ordinal)

    @visit.register
    def visit_Lambda(self, node: ast.Lambda, ordinal: int) -> None:
        if self.lambda_root:
            name = f"<anonymous>@{node.lineno}:{node.col_offset}"
            qualified_name = f"{self.lambda_root}.{name}"
            self.callables.append(
                PythonCallableCandidate(
                    node=node,
                    identity_node=node,
                    name=name,
                    qualified_name=qualified_name,
                    owner_name=self.lambda_owner,
                    ordinal=self.declaration_ordinal(node),
                    requires_call=True,
                    root_ordinal=self.lambda_root_ordinal,
                    sequence=ordinal,
                )
            )
            self.register_lambda(node, qualified_name, self.lambda_owner)
        self.enqueue(
            node,
            "nested",
            self.class_name,
            self.lambda_root,
            self.lambda_owner,
            self.lambda_root_ordinal,
        )

    @visit.register
    def visit_Assign(self, node: ast.Assign, ordinal: int) -> None:
        if self.parent_role == "module":
            for target in node.targets:
                self.visit_assignment_target(target, node, node.value)
        self.enqueue(
            node,
            "nested",
            self.class_name,
            self.lambda_root,
            self.lambda_owner,
            self.lambda_root_ordinal,
        )

    @visit.register
    def visit_AnnAssign(self, node: ast.AnnAssign, ordinal: int) -> None:
        if self.parent_role == "module":
            self.visit_annotated_target(node.target, node)
        self.enqueue(
            node,
            "nested",
            self.class_name,
            self.lambda_root,
            self.lambda_owner,
            self.lambda_root_ordinal,
        )

    @visit.register
    def visit_Import(self, node: ast.Import, ordinal: int) -> None:
        self.imports.extend(
            PythonImportCandidate(
                node=node,
                alias=alias,
                path=alias.name,
                is_relative=False,
                statement_id=ordinal,
            )
            for alias in node.names
        )
        self.enqueue(
            node,
            "nested",
            self.class_name,
            self.lambda_root,
            self.lambda_owner,
            self.lambda_root_ordinal,
        )

    @visit.register
    def visit_ImportFrom(self, node: ast.ImportFrom, ordinal: int) -> None:
        path = f"{'.' * node.level}{node.module or ''}"
        self.imports.extend(
            PythonImportCandidate(
                node=node,
                alias=alias,
                path=path,
                is_relative=node.level > 0,
                statement_id=ordinal,
            )
            for alias in node.names
        )
        self.enqueue(
            node,
            "nested",
            self.class_name,
            self.lambda_root,
            self.lambda_owner,
            self.lambda_root_ordinal,
        )

    def visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, ordinal: int) -> None:
        qualified_name = ""
        owner_name = ""
        if self.parent_role == "module":
            self.functions.append(PythonFunctionCandidate(node=node, ordinal=self.declaration_ordinal(node)))
            qualified_name = node.name
        elif self.parent_role in {"module_class", "nested_class"}:
            owner_name = self.class_name
            if self.parent_role == "module_class":
                qualified_name = f"{owner_name}.{node.name}"
        if qualified_name:
            self.callables.append(
                PythonCallableCandidate(
                    node=node,
                    identity_node=node,
                    name=node.name,
                    qualified_name=qualified_name,
                    owner_name=owner_name,
                    ordinal=self.declaration_ordinal(node),
                    requires_call=False,
                    root_ordinal=self.declaration_ordinal(node),
                    sequence=0,
                )
            )
            self.callable_names[node] = (qualified_name, owner_name)
            self.enqueue_function(node, qualified_name, owner_name, self.declaration_ordinal(node))
            return
        self.enqueue_function(node, self.lambda_root, self.lambda_owner, self.lambda_root_ordinal)

    def enqueue(
        self,
        node: ast.AST,
        role: str,
        class_name: str,
        lambda_root: str,
        lambda_owner: str,
        lambda_root_ordinal: int,
    ) -> None:
        self.queue.extend(
            (child, role, class_name, lambda_root, lambda_owner, lambda_root_ordinal)
            for child in ast.iter_child_nodes(node)
        )

    def enqueue_class(self, node: ast.ClassDef, role: str, class_name: str) -> None:
        body = set(node.body)
        for child in ast.iter_child_nodes(node):
            child_role = role if child in body else "nested"
            self.queue.append(
                (child, child_role, class_name, self.lambda_root, self.lambda_owner, self.lambda_root_ordinal)
            )

    def enqueue_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lambda_root: str,
        lambda_owner: str,
        lambda_root_ordinal: int,
    ) -> None:
        for child in ast.iter_child_nodes(node):
            self.queue.append((child, "nested", self.class_name, lambda_root, lambda_owner, lambda_root_ordinal))

    def inheritance_candidates(self) -> tuple[PythonInheritanceCandidate, ...]:
        return tuple(
            PythonInheritanceCandidate(source=candidate, base=base)
            for candidate in self.classes
            for base in candidate.node.bases
        )

    @singledispatchmethod
    def visit_assignment_target(self, target: ast.expr, statement: ast.Assign, value: ast.expr) -> None:
        return

    @visit_assignment_target.register
    def visit_assignment_name(self, target: ast.Name, statement: ast.Assign, value: ast.expr) -> None:
        candidate = PythonValueCandidate(
            statement=statement,
            target=target,
            ordinal=self.declaration_ordinal(target),
        )
        self.values.append(candidate)
        if target.id != "__all__":
            self.visit_assignment_value(value, candidate)

    @singledispatchmethod
    def visit_annotated_target(self, target: ast.expr, statement: ast.AnnAssign) -> None:
        return

    @visit_annotated_target.register
    def visit_annotated_name(self, target: ast.Name, statement: ast.AnnAssign) -> None:
        candidate = PythonValueCandidate(
            statement=statement,
            target=target,
            ordinal=self.declaration_ordinal(target),
        )
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

    def declaration_ordinal(self, node: ast.stmt | ast.expr) -> int:
        return (node.lineno << 32) + node.col_offset + 1
