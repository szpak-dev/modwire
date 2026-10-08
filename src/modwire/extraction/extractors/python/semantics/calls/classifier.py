import ast
from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.source_call import SourceCall
from ......shared.code.models.types import SourceCallResolution
from ...observations.call_candidate import PythonCallCandidate


class PythonCallTargetRule(ABC):
    @property
    @abstractmethod
    def order(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def applies(self, candidate: PythonCallCandidate) -> bool:
        raise NotImplementedError

    @abstractmethod
    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        raise NotImplementedError

    def source_call(
        self,
        candidate: PythonCallCandidate,
        target_callable_id: str,
        resolution: SourceCallResolution,
    ) -> SourceCall:
        expression = ast.unparse(candidate.node.func)
        target_name = self.node_name(candidate.node.func) or expression
        return SourceCall(
            source_callable_id=candidate.source_callable_id,
            target_callable_id=target_callable_id,
            source_id=candidate.source_id,
            line=candidate.node.lineno,
            expression=expression,
            resolution=resolution,
            target_name=target_name,
        )

    @singledispatchmethod
    def node_name(self, node: ast.AST) -> str:
        return ""

    @node_name.register
    def name_node_name(self, node: ast.Name) -> str:
        return node.id

    @node_name.register
    def attribute_node_name(self, node: ast.Attribute) -> str:
        parent = self.node_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr


class PythonCallTargetClassifier(ABC):
    @abstractmethod
    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        raise NotImplementedError


@injectable(as_type=PythonCallTargetClassifier)
@dataclass(frozen=True)
class OrderedPythonCallTargetClassifier(PythonCallTargetClassifier):
    rules: Mapping[Hashable, PythonCallTargetRule]

    def classify(self, candidate: PythonCallCandidate) -> SourceCall:
        for rule in sorted(self.rules.values(), key=lambda item: item.order):
            if rule.applies(candidate):
                return rule.classify(candidate)
        raise ValueError("No Python call-target rule accepted the candidate.")
