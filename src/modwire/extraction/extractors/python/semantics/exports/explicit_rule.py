from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_export import SourceExport
from ...observations.export_candidate import PythonExportCandidate
from .classifier import PythonExportRule


@injectable(as_type=PythonExportRule, qualifier="10-explicit")
@dataclass(frozen=True)
class ExplicitExportRule(PythonExportRule):
    @property
    def order(self) -> int:
        return 10

    def applies(self, candidate: PythonExportCandidate) -> bool:
        return candidate.explicit

    def classify(self, candidate: PythonExportCandidate) -> tuple[SourceExport, ...]:
        return super().classify(candidate)
