import ast
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from .classifier import PythonCallableRule


@injectable(as_type=PythonCallableRule, qualifier="50-function")
@dataclass(frozen=True)
class FunctionCallableRule(PythonCallableRule):
    @cached_property
    def node_kind_dispatch(self) -> Callable[[ast.AST, PythonCallableCandidate], SourceCallableKind]:
        return self.node_kind

    @property
    def order(self) -> int:
        return 50

    def applies(self, candidate: PythonCallableCandidate) -> bool:
        return True

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return self.node_kind_dispatch(candidate.node, candidate)

    @singledispatchmethod
    def node_kind(self, node: ast.AST, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return SourceCallableKind.FUNCTION

    @node_kind.register
    def lambda_kind(self, node: ast.Lambda, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return SourceCallableKind.ANONYMOUS if candidate.identity_node is node else SourceCallableKind.CALLABLE_VALUE
