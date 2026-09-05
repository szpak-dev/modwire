from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.boundaries.domain import FlowAnalyzerInterface
from modwire.architecture.boundaries.models.flow_violation import FlowViolation
from modwire.architecture.config.models.boundaries_config import BoundariesConfig
from modwire.architecture.config.models.boundary_rule import BoundaryRule
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.map.models.tag_match import TagMatch


@injectable(as_type=FlowAnalyzerInterface, qualifier="module_boundaries")
@dataclass(frozen=True)
class ModuleBoundaryAnalyzer(FlowAnalyzerInterface):
    @property
    def name(self) -> str:
        return "module-boundaries"

    @property
    def title(self) -> str:
        return "Module Boundary Violations"

    def analyze(self, architecture_map: ArchitectureMap, config: BoundariesConfig) -> tuple[FlowViolation, ...]:
        module_tag = architecture_map.realm.module_tag
        if not module_tag:
            return ()
        violations = [
            self.unclassified(source_id)
            for source_id in architecture_map.code_map.source_ids()
            if not self.matches(architecture_map, source_id, self.module_tags(config))
        ]
        for dependency in architecture_map.code_map.dependency_edges().all():
            edge = dependency.edge
            if edge.resolution != "resolved" or edge.to_id is None:
                continue
            source_tags = architecture_map.tag_map.tags_for(edge.from_id)
            target_tags = architecture_map.tag_map.tags_for(edge.to_id)
            source_modules = self.selected(source_tags, (module_tag,))
            target_modules = self.selected(target_tags, (module_tag,))
            if not source_modules and not target_modules:
                continue
            if self.same_module(source_modules, target_modules):
                continue
            rules = tuple(
                rule
                for rule in config.rules
                if (not rule.realm or rule.realm == architecture_map.realm.name)
                and any(match.name == rule.source for match in source_tags)
            )
            if any(self.allows(rule, source_tags, target_tags) for rule in rules):
                continue
            violations.append(
                FlowViolation(
                    violation_type=self.name,
                    path=(edge.from_id, edge.to_id),
                    violation_index=1,
                    rule_name=self.rule_name_for(rules),
                    message=self.message_for(rules, target_tags),
                    source_module=self.identities(source_modules),
                    target_module=self.identities(target_modules),
                )
            )
        return tuple(sorted(violations, key=lambda violation: violation.violation_key()))

    def module_tags(self, config: BoundariesConfig) -> tuple[str, ...]:
        values = [config.flow.module_tag]
        values.extend(realm.module_tag for realm in config.flow.realms)
        values.extend(config.flow.standalone_tags)
        return tuple(dict.fromkeys(value for value in values if value))

    def matches(
        self, architecture_map: ArchitectureMap, source_id: str, module_tags: tuple[str, ...]
    ) -> tuple[TagMatch, ...]:
        return self.selected(architecture_map.tag_map.tags_for(source_id), module_tags)

    def selected(self, matches: tuple[TagMatch, ...], names: tuple[str, ...]) -> tuple[TagMatch, ...]:
        wanted = set(names)
        return tuple(match for match in matches if match.name in wanted)

    def same_module(self, source_matches: tuple[TagMatch, ...], target_matches: tuple[TagMatch, ...]) -> bool:
        source = {self.identity(match) for match in source_matches}
        target = {self.identity(match) for match in target_matches}
        return bool(source.intersection(target))

    def allows(
        self, rule: BoundaryRule, source_matches: tuple[TagMatch, ...], target_matches: tuple[TagMatch, ...]
    ) -> bool:
        if any(match.name in rule.allow for match in target_matches):
            return True
        if not rule.allow_same_match:
            return False
        source = {self.identity(match) for match in source_matches if match.name == rule.source}
        target = {self.identity(match) for match in target_matches}
        return bool(source.intersection(target))

    def unclassified(self, source_id: str) -> FlowViolation:
        return FlowViolation(
            violation_type=self.name,
            path=(source_id,),
            violation_index=0,
            rule_name="boundary:unclassified",
            message="tracked file does not match an architecture module",
        )

    def identities(self, matches: tuple[TagMatch, ...]) -> str:
        return ",".join(sorted(self.identity(match) for match in matches))

    def identity(self, match: TagMatch) -> str:
        return f"{match.name}:{match.captured_path or match.name}"

    def rule_name_for(self, rules: tuple[BoundaryRule, ...]) -> str:
        if not rules:
            return "boundary:implicit-deny"
        return "boundary:" + ",".join(sorted({rule.source for rule in rules}))

    def message_for(self, rules: tuple[BoundaryRule, ...], target_matches: tuple[TagMatch, ...]) -> str:
        if any(match.name in rule.disallow for rule in rules for match in target_matches):
            return "tracked cross-module dependency matches an explicit disallow"
        return "tracked cross-module dependency is not explicitly allowed"
