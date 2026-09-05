from collections.abc import Callable, Iterable
from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.config.models.tag_rule import TagRule
from modwire.architecture.map.models.tag_map import TagMap
from modwire.architecture.map.models.tag_match import TagMatch
from modwire.shared.code.domain import PathMatcher


@injectable()
@dataclass(frozen=True)
class TagMatcher:
    paths: PathMatcher

    def map_for(self, node_ids: Iterable[str], tags: tuple[TagRule, ...]) -> TagMap:
        return TagMap(
            matches_by_node={node_id: matches for node_id in node_ids if (matches := self.tags_for(node_id, tags))}
        )

    def group_by_capture(self, tag_map: TagMap, tag_names: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
        return self._group_by_tag(tag_map, tag_names, key_for_match=lambda match: match.captured_path or match.name)

    def group_by_name(self, tag_map: TagMap, tag_names: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
        return self._group_by_tag(tag_map, tag_names, key_for_match=lambda match: match.name)

    def tags_for(self, node_id: str, tags: tuple[TagRule, ...]) -> tuple[TagMatch, ...]:
        return tuple(match for tag in tags if (match := self._match_rule(node_id, tag, scope=True)) is not None)

    def _group_by_tag(
        self, tag_map: TagMap, tag_names: tuple[str, ...], *, key_for_match: Callable[[TagMatch], str]
    ) -> dict[str, tuple[str, ...]]:
        if not tag_names:
            return {}
        wanted = set(tag_names)
        grouped: dict[str, list[str]] = {}
        for source_id, matches in tag_map.matches_by_node.items():
            for match in matches:
                if match.name in wanted:
                    grouped.setdefault(key_for_match(match), []).append(source_id)
        return {key: tuple(sorted(source_ids)) for key, source_ids in sorted(grouped.items())}

    def _match_rule(self, node_id: str, tag: TagRule, *, scope: bool) -> TagMatch | None:
        return self._match_pattern(node_id, tag.match, name=tag.name, scope=scope, exclude=tag.excluded_patterns)

    def _match_pattern(
        self, node_id: str, pattern: str, *, name: str, scope: bool, exclude: tuple[str, ...]
    ) -> TagMatch | None:
        normalized_node = self._normalize_path(node_id)
        normalized_pattern = self._normalize_path(pattern)
        if any(
            self._match_pattern(node_id, excluded, name=name, scope=scope, exclude=()) is not None
            for excluded in exclude
        ):
            return None
        wildcard_values = self.paths.match(normalized_node, normalized_pattern, scope=scope)
        if wildcard_values is None:
            return None
        return TagMatch(
            name=name,
            pattern=pattern,
            matched_path=normalized_node,
            captured_path="/".join(wildcard_values),
            is_wildcard=bool(wildcard_values),
            wildcard_values=wildcard_values,
        )

    def _normalize_path(self, value: str) -> str:
        return value.replace("\\", "/").strip("/")
