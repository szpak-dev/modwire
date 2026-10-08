import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.types import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from .classifier import PythonCallableRule


@injectable(as_type=PythonCallableRule, qualifier="50-function")
@dataclass(frozen=True)
class FunctionCallableRule(PythonCallableRule):
    @property
    def order(self) -> int:
        return 50

    def applies(self, candidate: PythonCallableCandidate) -> bool:
        return True

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        if candidate.requires_call:
            return "anonymous"
        if candidate.qualified_name == candidate.name:
            return "callable_value" if candidate.name != self.function_name(candidate) else "function"
        return "function"

    def function_name(self, candidate: PythonCallableCandidate) -> str:
        return self.node_name(candidate.node)

    @singledispatchmethod
    def node_name(self, node: ast.AST) -> str:
        return ""

    @node_name.register
    def function_node_name(self, node: ast.FunctionDef) -> str:
        return node.name

    @node_name.register
    def async_function_node_name(self, node: ast.AsyncFunctionDef) -> str:
        return node.name
