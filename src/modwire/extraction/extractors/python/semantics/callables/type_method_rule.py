import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_callable_kind import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from .classifier import PythonCallableRule


@injectable(as_type=PythonCallableRule, qualifier="20-type-method")
@dataclass(frozen=True)
class TypeMethodCallableRule(PythonCallableRule):
    @property
    def order(self) -> int:
        return 20

    def applies(self, candidate: PythonCallableCandidate) -> bool:
        return bool(candidate.owner_name) and self.has_decorator(candidate.node)

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return SourceCallableKind.TYPE_METHOD

    @singledispatchmethod
    def has_decorator(self, node: ast.AST) -> bool:
        return False

    @has_decorator.register
    def function_has_decorator(self, node: ast.FunctionDef) -> bool:
        return any(ast.unparse(item).rsplit(".", 1)[-1] == "classmethod" for item in node.decorator_list)

    @has_decorator.register
    def async_function_has_decorator(self, node: ast.AsyncFunctionDef) -> bool:
        return any(ast.unparse(item).rsplit(".", 1)[-1] == "classmethod" for item in node.decorator_list)
