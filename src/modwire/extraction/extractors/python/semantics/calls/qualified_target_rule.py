from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ...observations.call_candidate import PythonCallCandidate
from .classifier import PythonCallTargetRule


@injectable(as_type=PythonCallTargetRule, qualifier="10-qualified")
@dataclass(frozen=True)
class QualifiedCallTargetRule(PythonCallTargetRule):
    @property
    def order(self) -> int:
        return 10

    def applies(self, candidate: PythonCallCandidate) -> bool:
        return candidate.reference.expression in candidate.by_qualified_name

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        expression = candidate.reference.expression
        return self.source_call(candidate, candidate.by_qualified_name[expression], "resolved")
