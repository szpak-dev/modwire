from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_export import SourceExport
from ...observations.export_candidate import PythonExportCandidate


class PythonExportRule(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonExportCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(self, candidate: PythonExportCandidate) -> tuple[SourceExport, ...]:
        return (
            SourceExport(
                name=candidate.name,
                local_name=candidate.local_name,
                kind=candidate.kind,
                crossing_type="symbol",
                path=candidate.path,
                is_relative=candidate.is_relative,
                normalized_path=candidate.normalized_path,
                is_reexport=candidate.is_reexport,
                is_default=False,
                is_aliased=candidate.is_aliased,
                statement_id=candidate.statement_id,
            ),
        )


class PythonExportClassifier(ABC):
    @abstractmethod
    def classify(self, candidate: PythonExportCandidate) -> tuple[SourceExport, ...]:
        raise NotImplementedError


@injectable(as_type=PythonExportClassifier)
@dataclass(frozen=True)
class OrderedPythonExportClassifier(PythonExportClassifier):
    rules: Mapping[Hashable, PythonExportRule]

    def classify(self, candidate: PythonExportCandidate) -> tuple[SourceExport, ...]:
        for rule in sorted(self.rules.values(), key=lambda item: item.order):
            if rule.applies(candidate):
                return rule.classify(candidate)
        raise ValueError("No Python export rule accepted the candidate.")
