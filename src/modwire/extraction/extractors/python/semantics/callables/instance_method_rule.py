from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.types import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate
from .classifier import PythonCallableRule


@injectable(as_type=PythonCallableRule, qualifier="40-instance-method")
@dataclass(frozen=True)
class InstanceMethodCallableRule(PythonCallableRule):
    @property
    def order(self) -> int:
        return 40

    def applies(self, candidate: PythonCallableCandidate) -> bool:
        return bool(candidate.owner_name) and not candidate.requires_call

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        return "instance_method"
