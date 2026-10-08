import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="40-constructor")
@dataclass(frozen=True)
class ConstructorCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 40

    def applies(self, candidate: PythonCallCandidate) -> bool:
        return self.constructor_name(candidate.node.func) in candidate.constructors_by_name

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        name = self.constructor_name(candidate.node.func)
        return self.source_call(candidate, candidate.constructors_by_name[name], "resolved")

    @singledispatchmethod
    def constructor_name(self, node: ast.AST) -> str:
        return ""

    @constructor_name.register
    def named_constructor_name(self, node: ast.Name) -> str:
        return node.id

    @constructor_name.register
    def attribute_constructor_name(self, node: ast.Attribute) -> str:
        return node.attr
