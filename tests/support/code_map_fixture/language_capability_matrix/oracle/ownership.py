from dataclasses import dataclass

from modwire.application import DependencyGraph, FileId, SourceManifest


@dataclass(frozen=True)
class FixtureSourceOwnership:
    sources: frozenset[FileId]

    def accepts(self, graph: DependencyGraph, manifest: SourceManifest) -> bool:
        return (
            frozenset(graph.nodes) == self.sources
            and all(source == node.id for source, node in graph.nodes.items())
            and all(artifact.relative_path == artifact.source_id for artifact in manifest.sources)
            and all(
                edge.from_id in self.sources and (edge.to_id is None or edge.to_id in self.sources)
                for edge in graph.edges
            )
        )
