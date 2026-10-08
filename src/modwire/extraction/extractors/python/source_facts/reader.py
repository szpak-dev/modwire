from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ...models.parsed_source_file import ParsedSourceFile
from ..observations.source_context import PythonSourceContext
from ..semantics.catalog import PythonSemanticCatalog
from .contribution import PythonSourceFactContribution


class PythonSourceFactContributor(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def contribute(
        self,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSourceFactContribution:
        raise NotImplementedError


class PythonSourceFactReader(ABC):
    @abstractmethod
    def read(self, catalog: PythonSemanticCatalog, context: PythonSourceContext) -> ParsedSourceFile:
        raise NotImplementedError


@injectable(as_type=PythonSourceFactReader)
@dataclass(frozen=True)
class OrderedPythonSourceFactReader(PythonSourceFactReader):
    contributors: Mapping[Hashable, PythonSourceFactContributor]

    def read(self, catalog: PythonSemanticCatalog, context: PythonSourceContext) -> ParsedSourceFile:
        contribution = PythonSourceFactContribution()
        for contributor in sorted(self.contributors.values(), key=lambda item: item.order):
            contribution = contribution.combine(contributor.contribute(catalog, context))
        return contribution.parsed()
