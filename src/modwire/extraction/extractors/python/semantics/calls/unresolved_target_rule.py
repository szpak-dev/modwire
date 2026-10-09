from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ......shared.code.models.source_call_resolution import SourceCallResolution
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="50-unresolved")
@dataclass(frozen=True)
class UnresolvedCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 50

    def applies(self, candidate: PythonCallCandidate) -> bool:
        return candidate.reference.is_reference

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        return self.source_call(candidate, "", SourceCallResolution.UNRESOLVED)
