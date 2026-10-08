from abc import ABC, abstractmethod
from collections.abc import Collection, Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ......shared.code.models.types import SourceCallResolution
from ...observations.call_candidate import PythonCallCandidate


class PythonCallTargetRule(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonCallCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        raise NotImplementedError

    def source_call(
        self,
        candidate: PythonCallCandidate,
        target_callable_id: str,
        resolution: SourceCallResolution,
    ) -> SourceCall:
        return SourceCall(
            source_callable_id=candidate.source_callable_id,
            target_callable_id=target_callable_id,
            source_id=candidate.source_id,
            line=candidate.node.lineno,
            expression=candidate.reference.expression,
            resolution=resolution,
            target_name=candidate.reference.target_name or candidate.reference.expression,
        )


class PythonCallTargetClassifier(ABC):
    @abstractmethod
    def classify(self, candidates: Collection[PythonCallCandidate]) -> Collection[SourceCall]:
        raise NotImplementedError


@injectable(as_type=PythonCallTargetClassifier)
@dataclass(frozen=True)
class OrderedPythonCallTargetClassifier(PythonCallTargetClassifier):
    rules: Mapping[Hashable, PythonCallTargetRule]

    def classify(self, candidates: Collection[PythonCallCandidate]) -> Collection[SourceCall]:
        ordered_rules = tuple(sorted(self.rules.values(), key=lambda item: item.order))
        calls: list[SourceCall] = []
        for candidate in candidates:
            for rule in ordered_rules:
                if rule.applies(candidate):
                    calls.append(rule.classify(candidate))
                    break
            else:
                raise ValueError("No Python call-target rule accepted the candidate.")
        return tuple(calls)
