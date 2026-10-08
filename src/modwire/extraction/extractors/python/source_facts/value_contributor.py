from dataclasses import dataclass

from wireup import injectable

from ..observations.source_context import PythonSourceContext
from ..semantics.catalog import PythonSemanticCatalog
from .contribution import PythonSourceFactContribution
from .reader import PythonSourceFactContributor


@injectable(as_type=PythonSourceFactContributor, qualifier="30-value")
@dataclass(frozen=True)
class ValueFactContributor(PythonSourceFactContributor):
    @property
    def order(self) -> int:
        return 30

    def contribute(self, catalog: PythonSemanticCatalog, context: PythonSourceContext) -> PythonSourceFactContribution:
        return PythonSourceFactContribution(values=catalog.values)
