from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ...observations.class_candidate import PythonClassCandidate
from .classifier import PythonClassRule


@injectable(as_type=PythonClassRule, qualifier="20-concrete")
@dataclass(frozen=True)
class ConcreteClassRule(PythonClassRule):
    @property
    def order(self) -> int:
        return 20

    def applies(self, candidate: PythonClassCandidate) -> bool:
        return True

    def classify(self, candidate: PythonClassCandidate) -> DeclarationFamily:
        return DeclarationFamily.CLASS
