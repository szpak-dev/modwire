import ast
from collections import deque
from dataclasses import dataclass

from wireup import injectable

from .domain import PythonSyntaxObserver
from .syntax_observation import PythonSyntaxObservation


@injectable(as_type=PythonSyntaxObserver)
@dataclass(frozen=True)
class OrderedSyntaxObserver(PythonSyntaxObserver):
    def observe(self, tree: ast.Module) -> PythonSyntaxObservation:
        nodes: list[ast.AST] = []
        callable_collection_roots = {
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        module_class_methods = {
            child
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        callable_collection_roots.update(module_class_methods)
        descendant_targets: set[ast.FunctionDef | ast.AsyncFunctionDef] = set()
        lambdas_by_node: dict[ast.AST, list[ast.Lambda]] = {}
        pending = deque(((tree, None),))
        while pending:
            node, inherited_collection_root = pending.popleft()
            collection_root = node if node in callable_collection_roots else inherited_collection_root
            nodes.append(node)
            if isinstance(node, ast.ClassDef):
                descendant_targets.update(
                    child
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
            if isinstance(node, ast.Lambda) and collection_root is not None:
                lambdas_by_node.setdefault(collection_root, []).append(node)
            pending.extend((child, collection_root) for child in ast.iter_child_nodes(node))
        observed_nodes = tuple(nodes)
        nodes.clear()

        ordered_nodes: list[ast.AST] = []
        descendant_spans: dict[ast.AST, tuple[int, int]] = {}
        calls_by_node: dict[ast.AST, list[ast.Call]] = {}
        lambdas_with_calls: set[ast.Lambda] = set()
        active_lambdas: list[tuple[ast.Lambda, bool]] = []
        traversal: list[
            tuple[
                ast.AST,
                ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | None,
                bool,
                int,
            ]
        ] = [(tree, None, False, 0)]
        while traversal:
            node, owner, completed, descendant_start = traversal.pop()
            if completed:
                if node in descendant_targets:
                    descendant_spans[node] = (descendant_start, len(ordered_nodes))
                if isinstance(node, ast.Lambda):
                    lambda_node, lambda_has_calls = active_lambdas.pop()
                    if lambda_has_calls:
                        lambdas_with_calls.add(lambda_node)
                        if active_lambdas:
                            outer_lambda, _ = active_lambdas[-1]
                            active_lambdas[-1] = (outer_lambda, True)
                continue

            ordered_nodes.append(node)
            if isinstance(node, ast.Call) and owner is not None:
                calls_by_node.setdefault(owner, []).append(node)
            if isinstance(node, ast.Call) and active_lambdas:
                active_lambda, _ = active_lambdas[-1]
                active_lambdas[-1] = (active_lambda, True)

            if isinstance(node, ast.Lambda):
                active_lambdas.append((node, False))
            if node in descendant_targets or isinstance(node, ast.Lambda):
                traversal.append((node, owner, True, len(ordered_nodes)))

            children = tuple(ast.iter_child_nodes(node))
            if isinstance(node, ast.ClassDef):
                traversal.extend((child, None, False, 0) for child in reversed(children))
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_children = frozenset(node.body)
                traversal.extend(
                    (child, node if child in body_children else None, False, 0) for child in reversed(children)
                )
                continue
            if isinstance(node, ast.Lambda):
                traversal.extend(
                    (child, node if child is node.body else None, False, 0) for child in reversed(children)
                )
                continue
            traversal.extend((child, owner, False, 0) for child in reversed(children))
        ordered_node_sequence = tuple(ordered_nodes)
        ordered_nodes.clear()

        return PythonSyntaxObservation(
            nodes=observed_nodes,
            _ordered_nodes=ordered_node_sequence,
            _descendant_spans=descendant_spans,
            _calls_by_node={node: tuple(calls) for node, calls in calls_by_node.items()},
            _lambdas_by_node={node: tuple(lambdas) for node, lambdas in lambdas_by_node.items()},
            _lambdas_with_calls=frozenset(lambdas_with_calls),
        )
