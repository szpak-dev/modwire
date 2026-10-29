from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ......shared.code.models.source_call_resolution import SourceCallResolution
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="10-qualified")
@dataclass(frozen=True)
class QualifiedCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 10

    def applies(self, candidate: PythonCallCandidate) -> bool:
        expression = candidate.reference.expression
        return expression in candidate.by_qualified_name and len(candidate.by_qualified_name[expression]) == 1

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        expression = candidate.reference.expression
        return self.source_call(candidate, candidate.by_qualified_name[expression][0], SourceCallResolution.RESOLVED)
