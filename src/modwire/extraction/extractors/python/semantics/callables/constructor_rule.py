from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from .classifier import PythonCallableRule


@injectable(as_type=PythonCallableRule, qualifier="35-constructor")
@dataclass(frozen=True)
class ConstructorCallableRule(PythonCallableRule):
    @property
    def order(self) -> int:
        return 35

    def applies(self, candidate: PythonCallableCandidate) -> bool:
        return self.is_class_scope(candidate.binding_scope) and candidate.name == "__init__"

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return SourceCallableKind.CONSTRUCTOR
