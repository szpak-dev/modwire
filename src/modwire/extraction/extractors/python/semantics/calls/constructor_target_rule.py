from dataclasses import dataclass

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
        return candidate.reference.constructor_name in candidate.constructors_by_name

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        name = candidate.reference.constructor_name
        return self.source_call(candidate, candidate.constructors_by_name[name], "resolved")
