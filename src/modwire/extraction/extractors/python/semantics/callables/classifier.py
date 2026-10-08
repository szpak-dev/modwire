from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.types import SourceCallableKind
from ...observations.callable_candidate import PythonCallableCandidate


class PythonCallableRule(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonCallableCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        raise NotImplementedError


class PythonCallableClassifier(ABC):
    @abstractmethod
    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        raise NotImplementedError


@injectable(as_type=PythonCallableClassifier)
@dataclass(frozen=True)
class OrderedPythonCallableClassifier(PythonCallableClassifier):
    rules: Mapping[Hashable, PythonCallableRule]

    def classify(self, candidate: PythonCallableCandidate) -> SourceCallableKind:
        for rule in sorted(self.rules.values(), key=lambda item: item.order):
            if rule.applies(candidate):
                return rule.classify(candidate)
        raise ValueError("No Python callable rule accepted the candidate.")
