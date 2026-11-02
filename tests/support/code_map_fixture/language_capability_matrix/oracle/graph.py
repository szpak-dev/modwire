from dataclasses import dataclass

from modwire.application import DependencyGraph, FileId


@dataclass(frozen=True)
class FixtureGraphOwnership:
    sources: frozenset[FileId]

    def accepts(self, graph: DependencyGraph) -> bool:
        return frozenset(graph.nodes) == self.sources and all(
            edge.from_id in self.sources and (edge.to_id is None or edge.to_id in self.sources) for edge in graph.edges
        )
