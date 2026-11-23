from abc import ABC, abstractmethod
from collections.abc import Collection
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.callables.source_call import SourceCall
from ......shared.code.models.callables.source_call_resolution import SourceCallResolution
from ......shared.code.models.declarations.source_binding_kind import SourceBindingKind
from ......shared.code.models.declarations.source_unresolved_reason import SourceUnresolvedReason
from ...observations.call_candidate import PythonCallCandidate


class PythonCallTargetClassifier(ABC):
    @abstractmethod
    def classify(self, candidates: Collection[PythonCallCandidate]) -> Collection[SourceCall]:
        raise NotImplementedError


@injectable(as_type=PythonCallTargetClassifier)
@dataclass(frozen=True)
class ResolvedPythonCallTargetClassifier(PythonCallTargetClassifier):
    def classify(self, candidates: Collection[PythonCallCandidate]) -> Collection[SourceCall]:
        calls: list[SourceCall] = []
        for candidate in candidates:
            target = candidate.target
            resolution = SourceCallResolution.RESOLVED
            target_id = None
            if target.kind is SourceBindingKind.RESOLVED:
                target_id = target.declaration_id
            else:
                resolution = (
                    SourceCallResolution.DYNAMIC
                    if target.reason is SourceUnresolvedReason.DYNAMIC
                    else SourceCallResolution.UNRESOLVED
                )
            calls.append(
                SourceCall(
                    source_callable_id=candidate.source_callable_id,
                    ordinal=candidate.ordinal,
                    target_callable_id=target_id,
                    source_id=candidate.source_callable_id.source_id,
                    line=candidate.node.lineno,
                    expression=candidate.reference.expression,
                    resolution=resolution,
                    target_name=candidate.reference.target_name,
                )
            )
        return tuple(calls)
