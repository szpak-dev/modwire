import ast
from abc import ABC, abstractmethod

from ....shared.code.models.source_assigned_value import SourceAssignedValue
from .call_context import PythonCallContext


class PythonCallReader(ABC):
    @abstractmethod
    def collect(self, node: ast.AST, context: PythonCallContext) -> list[dict[str, object]]:
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
