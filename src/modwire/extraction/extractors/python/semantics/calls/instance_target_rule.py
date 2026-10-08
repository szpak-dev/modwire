from dataclasses import dataclass

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
        qualified_name = candidate.reference.instance_qualified_name
        return bool(qualified_name) and qualified_name in candidate.by_qualified_name

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        qualified_name = candidate.reference.instance_qualified_name
        return self.source_call(candidate, candidate.by_qualified_name[qualified_name], "resolved")
