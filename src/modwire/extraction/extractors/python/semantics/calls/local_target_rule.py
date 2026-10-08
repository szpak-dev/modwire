import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="20-local")
@dataclass(frozen=True)
class LocalCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 20

    def applies(self, candidate: PythonCallCandidate) -> bool:
        return self.local_name(candidate.node.func) in candidate.by_name

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        name = self.local_name(candidate.node.func)
        return self.source_call(candidate, candidate.by_name[name], "resolved")

    @singledispatchmethod
    def local_name(self, node: ast.AST) -> str:
        return ""

    @local_name.register
    def named_local_name(self, node: ast.Name) -> str:
        return node.id
