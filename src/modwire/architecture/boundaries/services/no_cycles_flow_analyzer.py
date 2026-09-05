from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.boundaries.domain import BaseFlowAnalyzer, FlowAnalyzerInterface
from modwire.architecture.boundaries.models.flow_violation import FlowViolation
from modwire.architecture.config.models.boundaries_config import BoundariesConfig
from modwire.architecture.map.models.architecture_map import ArchitectureMap


@injectable(as_type=FlowAnalyzerInterface, qualifier="no_cycles")
@dataclass(frozen=True)
class NoCyclesFlowAnalyzer(FlowAnalyzerInterface, BaseFlowAnalyzer):
    @property
    def name(self) -> str:
        return "no-cycles"

    @property
    def title(self) -> str:
        return "Cycle Violations"

    def analyze(self, architecture_map: ArchitectureMap, config: BoundariesConfig) -> tuple[FlowViolation, ...]:
        if not architecture_map.realm.module_tag:
            return ()
        adjacency = self.module_adjacency(architecture_map)
        emitted: set[tuple[str, ...]] = set()
        violations: list[FlowViolation] = []
        for module in sorted(adjacency):
            self.walk_modules(
                architecture_map=architecture_map,
                adjacency=adjacency,
                module=module,
                path=(module,),
                emitted=emitted,
                violations=violations,
            )
        return tuple(violations)

    def module_adjacency(self, architecture_map: ArchitectureMap) -> dict[str, set[str]]:
        adjacency: dict[str, set[str]] = {}
        for dependency in architecture_map.code_map.dependency_edges().all():
            if dependency.edge.to_id is None:
                continue
            source = self.module_for(architecture_map, dependency.edge.from_id)
            target = self.module_for(architecture_map, dependency.edge.to_id)
            if not source or not target or source == target:
                continue
            adjacency.setdefault(source, set()).add(target)
        return adjacency

    def walk_modules(
        self,
        architecture_map: ArchitectureMap,
        adjacency: dict[str, set[str]],
        module: str,
        path: tuple[str, ...],
        emitted: set[tuple[str, ...]],
        violations: list[FlowViolation],
    ) -> None:
        for target in sorted(adjacency.get(module, ())):
            if target in path:
                cycle = (*path[path.index(target) :], target)
                canonical = self.canonical_cycle(cycle)
                if canonical in emitted:
                    continue
                emitted.add(canonical)
                violations.append(
                    FlowViolation(
                        violation_type=self.name,
                        path=canonical,
                        violation_index=len(canonical) - 1,
                        rule_name=self.rule_name(architecture_map),
                        message="module cycle detected",
                    )
                )
                continue
            self.walk_modules(
                architecture_map=architecture_map,
                adjacency=adjacency,
                module=target,
                path=(*path, target),
                emitted=emitted,
                violations=violations,
            )

    def canonical_cycle(self, cycle: tuple[str, ...]) -> tuple[str, ...]:
        ring = cycle[:-1]
        rotations = tuple(ring[index:] + ring[:index] for index in range(len(ring)))
        first = min(rotations)
        return (*first, first[0])
