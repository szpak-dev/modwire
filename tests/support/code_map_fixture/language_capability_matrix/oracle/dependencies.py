from dataclasses import dataclass

from modwire.application import Edge, Node


@dataclass(frozen=True)
class FixtureDependencyObservation:
    node: Node
    edges: tuple[Edge, ...]
