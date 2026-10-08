from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass

from wireup import injectable

from ..observations.source_context import PythonSourceContext
from ..observations.source_observation import PythonSourceObservation
from .catalog import PythonSemanticCatalog
from .contribution import PythonSemanticContribution


class PythonSemanticContributor(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        raise NotImplementedError


class PythonSemanticReader(ABC):
    @abstractmethod
    def read(self, observation: PythonSourceObservation, context: PythonSourceContext) -> PythonSemanticCatalog:
        raise NotImplementedError


@injectable(as_type=PythonSemanticReader)
@dataclass(frozen=True)
class OrderedPythonSemanticReader(PythonSemanticReader):
    contributors: Mapping[Hashable, PythonSemanticContributor]

    def read(self, observation: PythonSourceObservation, context: PythonSourceContext) -> PythonSemanticCatalog:
        catalog = PythonSemanticCatalog()
        for contributor in sorted(self.contributors.values(), key=lambda item: item.order):
            catalog = catalog.combine(contributor.contribute(observation, catalog, context))
        return catalog
