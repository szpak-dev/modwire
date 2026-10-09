from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ......shared.code.models.source_call_resolution import SourceCallResolution
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="20-local")
@dataclass(frozen=True)
class LocalCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 20

    def applies(self, candidate: PythonCallCandidate) -> bool:
        return candidate.reference.local_name in candidate.by_name

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        name = candidate.reference.local_name
        return self.source_call(candidate, candidate.by_name[name], SourceCallResolution.RESOLVED)
