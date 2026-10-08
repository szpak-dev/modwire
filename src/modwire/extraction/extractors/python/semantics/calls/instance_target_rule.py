import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="30-instance")
@dataclass(frozen=True)
class InstanceCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 30

    def applies(self, candidate: PythonCallCandidate) -> bool:
        qualified_name = self.qualified_name(candidate.node.func, candidate.owner_name)
        return bool(qualified_name) and qualified_name in candidate.by_qualified_name

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        qualified_name = self.qualified_name(candidate.node.func, candidate.owner_name)
        return self.source_call(candidate, candidate.by_qualified_name[qualified_name], "resolved")

    @singledispatchmethod
    def qualified_name(self, node: ast.AST, owner_name: str) -> str:
        return ""

    @qualified_name.register
    def attribute_qualified_name(self, node: ast.Attribute, owner_name: str) -> str:
        if self.is_receiver(node.value):
            return ".".join(part for part in (owner_name, node.attr) if part)
        return ""

    @singledispatchmethod
    def is_receiver(self, node: ast.AST) -> bool:
        return False

    @is_receiver.register
    def name_is_receiver(self, node: ast.Name) -> bool:
        return node.id in {"self", "cls"}
