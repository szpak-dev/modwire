import ast
from abc import ABC, abstractmethod

from ....shared.code.models.source_assigned_value import SourceAssignedValue
from .call_context import PythonCallContext
from .syntax_observation import PythonSyntaxObservation


class PythonCallReader(ABC):
    @abstractmethod
    def collect(self, nodes: tuple[ast.Call, ...], context: PythonCallContext) -> list[dict[str, object]]:
        raise NotImplementedError


class PythonSyntaxObserver(ABC):
    @abstractmethod
    def observe(self, tree: ast.Module) -> PythonSyntaxObservation:
        raise NotImplementedError


class PythonExpressionReferenceReader(ABC):
    @abstractmethod
    def read(self, node: ast.expr) -> str:
        raise NotImplementedError


class PythonAssignedValueReader(ABC):
    @abstractmethod
    def read(self, node: ast.expr) -> SourceAssignedValue:
        raise NotImplementedError

    @abstractmethod
    def unassigned(self) -> SourceAssignedValue:
        raise NotImplementedError
