from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.config.models.boundaries_config import BoundariesConfig
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.map.models.architecture_realm import ArchitectureRealm
from modwire.architecture.map.services.tag_matcher import TagMatcher
from modwire.shared.code.models.queryable_code_map import QueryableCodeMap

from ..domain import ArchitectureMapper


@injectable(as_type=ArchitectureMapper)
@dataclass(frozen=True)
class ArchitectureMapLoader(ArchitectureMapper):
    matcher: TagMatcher

    def default_realm(self, config: BoundariesConfig) -> ArchitectureRealm:
        flow = config.flow
        return ArchitectureRealm(name="", module_tag=flow.module_tag, layers=flow.layers)

    def load(self, code_map: QueryableCodeMap, config: BoundariesConfig) -> ArchitectureMap:
        source_ids = tuple(code_map.source_ids())
        tag_map = self.matcher.map_for(source_ids, config.tags)
        return ArchitectureMap(
            code_map=code_map,
            tag_map=tag_map,
            modules=self.matcher.group_by_capture(tag_map, self.module_tags(config)),
            layers=self.matcher.group_by_name(tag_map, self.layer_tags(config)),
            unknown_files=tuple(source_id for source_id in source_ids if source_id not in tag_map.matches_by_node),
            realm=self.default_realm(config),
        )

    def module_tags(self, config: BoundariesConfig) -> tuple[str, ...]:
        tags = [config.flow.module_tag]
        tags.extend(realm.module_tag for realm in config.flow.realms)
        return self.unique_non_empty(tags)

    def layer_tags(self, config: BoundariesConfig) -> tuple[str, ...]:
        tags = [*config.flow.layers]
        for realm in config.flow.realms:
            tags.extend(realm.layers)
        return self.unique_non_empty(tags)

    def unique_non_empty(self, values: list[str]) -> tuple[str, ...]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return tuple(result)
