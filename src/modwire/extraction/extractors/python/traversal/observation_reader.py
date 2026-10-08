import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ..observations.call_observation import PythonCallObservation
from ..observations.source_observation import PythonSourceObservation
from .breadth_first_visitor import BreadthFirstObservationVisitor
from .depth_first_visitor import DepthFirstObservationVisitor


class PythonObservationReader(ABC):
    @abstractmethod
    def read(self, tree: ast.Module) -> PythonSourceObservation:
        raise NotImplementedError


@injectable(as_type=PythonObservationReader)
@dataclass(frozen=True)
class LinearPythonObservationReader(PythonObservationReader):
    def read(self, tree: ast.Module) -> PythonSourceObservation:
        breadth_first = BreadthFirstObservationVisitor()
        breadth_observation = breadth_first.read(tree)
        depth_first = DepthFirstObservationVisitor(
            callable_names=breadth_first.callable_names,
            lambda_names=breadth_first.lambda_names,
        )
        depth_observation = depth_first.read(tree)
        callables = tuple(
            sorted(
                (
                    candidate
                    for candidate in breadth_observation.callables
                    if (not candidate.requires_call) or candidate.node in depth_first.lambdas_with_calls
                ),
                key=lambda candidate: (candidate.root_ordinal, candidate.sequence),
            )
        )
        call_sites = tuple(
            PythonCallObservation(
                node=node,
                source_qualified_name=candidate.qualified_name,
                owner_name=candidate.owner_name,
            )
            for candidate in callables
            for node in (depth_first.calls[candidate.node] if candidate.node in depth_first.calls else ())
        )
        return PythonSourceObservation(
            classes=breadth_observation.classes,
            functions=breadth_observation.functions,
            values=breadth_observation.values,
            callables=callables,
            calls=call_sites,
            imports=breadth_observation.imports,
            exports=breadth_observation.exports,
            properties=depth_observation.properties,
            inheritance=breadth_observation.inheritance,
        )
