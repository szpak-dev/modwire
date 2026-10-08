import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="50-unresolved")
@dataclass(frozen=True)
class UnresolvedCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 50

    def applies(self, candidate: PythonCallCandidate) -> bool:
        return self.is_reference(candidate.node.func)

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        return self.source_call(candidate, "", "unresolved")

    @singledispatchmethod
    def is_reference(self, node: ast.AST) -> bool:
        return False

    @is_reference.register
    def name_is_reference(self, node: ast.Name) -> bool:
        return True

    @is_reference.register
    def attribute_is_reference(self, node: ast.Attribute) -> bool:
        return True
