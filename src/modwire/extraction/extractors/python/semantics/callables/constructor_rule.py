from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.types import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from .classifier import PythonCallableRule


@injectable(as_type=PythonCallableRule, qualifier="10-constructor")
@dataclass(frozen=True)
class ConstructorCallableRule(PythonCallableRule):
    @property
    def order(self) -> int:
        return 10

    def applies(self, candidate: PythonCallableCandidate) -> bool:
        return bool(candidate.owner_name) and candidate.name == "__init__"

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return "constructor"
