from typing import Literal

from modwire.application import CodeMap, FileId

from ....fixture_model import FixtureModel
from ..dependencies import FixtureDependencyObservation
from ..identities import FixtureSourceIdentities
from ..observation import PublicFactObservation


class DependencySelector(FixtureModel):
    kind: Literal["dependencies"]
    source: FileId

    def read_expected(self, code_map: CodeMap) -> PublicFactObservation:
        return PublicFactObservation(
            FixtureDependencyObservation(
                node=code_map.dependency_graph.nodes[self.source],
                edges=tuple(edge for edge in code_map.dependency_graph.edges if edge.from_id == self.source),
            )
        )

    def read_actual(self, code_map: CodeMap, identities: FixtureSourceIdentities) -> PublicFactObservation:
        authored = identities.authored(self.source)
        return PublicFactObservation(
            FixtureDependencyObservation(
                node=identities.node(code_map.dependency_graph.nodes[authored]),
                edges=tuple(
                    identities.edge(edge) for edge in code_map.dependency_graph.edges if edge.from_id == authored
                ),
            )
        )
