from ....shared.values.models.value_model import ValueModel
from .tag_match import TagMatch


class TagMap(ValueModel):
    matches_by_node: dict[str, tuple[TagMatch, ...]]

    def tags_for(self, node_id: str) -> tuple[TagMatch, ...]:
        return self.matches_by_node.get(node_id, ())

    def first_match(self, node_id: str, names: tuple[str, ...]) -> TagMatch | None:
        wanted = set(names)
        return next((match for match in self.tags_for(node_id) if match.name in wanted), None)

    def matches(self, node_id: str, name: str) -> tuple[TagMatch, ...]:
        return tuple(match for match in self.tags_for(node_id) if match.name == name)
