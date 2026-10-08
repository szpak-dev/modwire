from dataclasses import dataclass

from wireup import injectable

from ..observations.source_context import PythonSourceContext
from ..semantics.catalog import PythonSemanticCatalog
from .contribution import PythonSourceFactContribution
from .reader import PythonSourceFactContributor


@injectable(as_type=PythonSourceFactContributor, qualifier="10-class")
@dataclass(frozen=True)
class ClassFactContributor(PythonSourceFactContributor):
    @property
    def order(self) -> int:
        return 10

    def contribute(self, catalog: PythonSemanticCatalog, context: PythonSourceContext) -> PythonSourceFactContribution:
        return PythonSourceFactContribution(classes=catalog.classes, abstract_classes=catalog.abstract_classes)
