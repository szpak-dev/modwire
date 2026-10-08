from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ...observations.class_candidate import PythonClassCandidate


class PythonClassRule(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonClassCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(self, candidate: PythonClassCandidate) -> DeclarationFamily:
        raise NotImplementedError


class PythonClassClassifier(ABC):
    @abstractmethod
    def classify(self, candidate: PythonClassCandidate) -> DeclarationFamily:
        raise NotImplementedError


@injectable(as_type=PythonClassClassifier)
@dataclass(frozen=True)
class OrderedPythonClassClassifier(PythonClassClassifier):
    rules: Mapping[Hashable, PythonClassRule]

    def classify(self, candidate: PythonClassCandidate) -> DeclarationFamily:
        for rule in sorted(self.rules.values(), key=lambda item: item.order):
            if rule.applies(candidate):
                return rule.classify(candidate)
        raise ValueError("No Python class rule accepted the candidate.")
