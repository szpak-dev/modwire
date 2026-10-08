from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="60-dynamic")
@dataclass(frozen=True)
class DynamicCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 60

    def applies(self, candidate: PythonCallCandidate) -> bool:
        return True

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        return self.source_call(candidate, "", "dynamic")
