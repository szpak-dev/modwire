import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ...observations.call_observation import PythonCallObservation
from ...observations.call_reference import PythonCallReference


class PythonCallReferenceReader(ABC):
    @abstractmethod
    def read(self, observation: PythonCallObservation) -> PythonCallReference:
        raise NotImplementedError


@injectable(as_type=PythonCallReferenceReader)
@dataclass(frozen=True)
class SyntaxCallReferenceReader(PythonCallReferenceReader):
    def read(self, observation: PythonCallObservation) -> PythonCallReference:
        return self.read_expression(observation.node.func)

    @singledispatchmethod
    def read_expression(self, node: ast.expr) -> PythonCallReference:
        expression = ast.unparse(node)
        return PythonCallReference(
            expression=expression,
            target_name=expression,
            is_reference=False,
        )

    @read_expression.register
    def read_name(self, node: ast.Name) -> PythonCallReference:
        return PythonCallReference(
            expression=node.id,
            target_name=node.id,
            is_reference=True,
        )

    @read_expression.register
    def read_attribute(self, node: ast.Attribute) -> PythonCallReference:
        expression = ast.unparse(node)
        return PythonCallReference(
            expression=expression,
            target_name=self.attribute_name(node),
            is_reference=True,
        )

    @singledispatchmethod
    def attribute_name(self, node: ast.expr) -> str:
        return ""

    @attribute_name.register
    def name_attribute_name(self, node: ast.Name) -> str:
        return node.id

    @attribute_name.register
    def nested_attribute_name(self, node: ast.Attribute) -> str:
        parent = self.attribute_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
