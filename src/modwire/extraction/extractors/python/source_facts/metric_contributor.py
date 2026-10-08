from dataclasses import dataclass

from wireup import injectable

from ..observations.source_context import PythonSourceContext
from ..semantics.catalog import PythonSemanticCatalog
from .contribution import PythonSourceFactContribution
from .reader import PythonSourceFactContributor


@injectable(as_type=PythonSourceFactContributor, qualifier="100-metric")
@dataclass(frozen=True)
class MetricFactContributor(PythonSourceFactContributor):
    @property
    def order(self) -> int:
        return 100

    def contribute(self, catalog: PythonSemanticCatalog, context: PythonSourceContext) -> PythonSourceFactContribution:
        return PythonSourceFactContribution(
            line_count=catalog.line_count,
            code_line_count=catalog.code_line_count,
            public_symbol_count=catalog.public_symbol_count,
        )
