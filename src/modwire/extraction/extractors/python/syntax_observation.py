import ast
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PythonSyntaxObservation:
    nodes: tuple[ast.AST, ...]
    _ordered_nodes: tuple[ast.AST, ...] = field(repr=False)
    _descendant_spans: dict[ast.AST, tuple[int, int]] = field(repr=False)
    _calls_by_node: dict[ast.AST, tuple[ast.Call, ...]] = field(repr=False)
    _lambdas_by_node: dict[ast.AST, tuple[ast.Lambda, ...]] = field(repr=False)
    _lambdas_with_calls: frozenset[ast.Lambda] = field(repr=False)

    def descendants(self, node: ast.AST) -> tuple[ast.AST, ...]:
        start, end = self._descendant_spans[node]
        return self._ordered_nodes[start:end]

    def calls(self, node: ast.AST) -> tuple[ast.Call, ...]:
        return self._calls_by_node.get(node, ())

    def lambdas(self, node: ast.AST) -> tuple[ast.Lambda, ...]:
        return self._lambdas_by_node.get(node, ())

    def has_calls(self, node: ast.AST) -> bool:
        return node in self._lambdas_with_calls
