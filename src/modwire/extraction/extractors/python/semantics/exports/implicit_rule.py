from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_export import SourceExport
from ...observations.export_candidate import PythonExportCandidate
from .classifier import PythonExportRule


@injectable(as_type=PythonExportRule, qualifier="20-implicit")
@dataclass(frozen=True)
class ImplicitExportRule(PythonExportRule):
    @property
    def order(self) -> int:
        return 20

    def applies(self, candidate: PythonExportCandidate) -> bool:
        return not candidate.explicit

    def classify(self, candidate: PythonExportCandidate) -> tuple[SourceExport, ...]:
        return super().classify(candidate)
