from dataclasses import dataclass

from wireup import injectable

from ..observations.source_context import PythonSourceContext
from ..semantics.catalog import PythonSemanticCatalog
from .contribution import PythonSourceFactContribution
from .reader import PythonSourceFactContributor


@injectable(as_type=PythonSourceFactContributor, qualifier="20-function")
@dataclass(frozen=True)
class FunctionFactContributor(PythonSourceFactContributor):
    @property
    def order(self) -> int:
        return 20

    def contribute(self, catalog: PythonSemanticCatalog, context: PythonSourceContext) -> PythonSourceFactContribution:
        return PythonSourceFactContribution(functions=catalog.functions)
