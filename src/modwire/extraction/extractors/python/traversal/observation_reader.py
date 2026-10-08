import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ..observations.source_observation import PythonSourceObservation
from .ordered_observation_visitor import OrderedObservationVisitor


class PythonObservationReader(ABC):
    @abstractmethod
    def read(self, tree: ast.Module) -> PythonSourceObservation:
        raise NotImplementedError


@injectable(as_type=PythonObservationReader)
@dataclass(frozen=True)
class LinearPythonObservationReader(PythonObservationReader):
    def read(self, tree: ast.Module) -> PythonSourceObservation:
        return OrderedObservationVisitor().read(tree)
