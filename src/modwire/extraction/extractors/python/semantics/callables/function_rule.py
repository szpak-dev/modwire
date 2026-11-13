import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
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
        return self.node_kind(candidate.node, candidate)

    @singledispatchmethod
    def node_kind(self, node: ast.AST, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return SourceCallableKind.FUNCTION

    @node_kind.register
    def lambda_kind(self, node: ast.Lambda, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return SourceCallableKind.ANONYMOUS if candidate.identity_node is node else SourceCallableKind.CALLABLE_VALUE
