import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from .classifier import PythonCallableRule


@injectable(as_type=PythonCallableRule, qualifier="40-instance-method")
@dataclass(frozen=True)
class InstanceMethodCallableRule(PythonCallableRule):
    @property
    def order(self) -> int:
        return 40

    def applies(self, candidate: PythonCallableCandidate) -> bool:
        return self.is_class_scope(candidate.binding_scope) and self.is_function(candidate.node)

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return SourceCallableKind.INSTANCE_METHOD

    @singledispatchmethod
    def is_function(self, node: ast.AST) -> bool:
        return False

    @is_function.register(ast.FunctionDef)
    @is_function.register(ast.AsyncFunctionDef)
    def function_node(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return True
