from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import FileId
from ...config.models.boundaries_config import BoundariesConfig
from ...map.models.architecture_map import ArchitectureMap
from ..domain import BaseFlowAnalyzer, FlowAnalyzerInterface
from ..models.flow_violation import FlowViolation


@dataclass(frozen=True)
class NoReentryTraversalState:
    source_id: str
    exited_modules: frozenset[str]


@injectable(as_type=FlowAnalyzerInterface, qualifier="no_reentry")
@dataclass(frozen=True)
class NoReentryFlowAnalyzer(FlowAnalyzerInterface, BaseFlowAnalyzer):
    @property
    def name(self) -> str:
        return "no-reentry"

    @property
    def title(self) -> str:
        return "No Re-Entry Violations"

    def analyze(self, architecture_map: ArchitectureMap, config: BoundariesConfig) -> tuple[FlowViolation, ...]:
        if not architecture_map.realm.module_tag:
            return ()
        violations: list[FlowViolation] = []
        visited: set[NoReentryTraversalState] = set()
        for root in self.roots(architecture_map):
            self.walk_dependencies(
                architecture_map=architecture_map,
                source_id=root,
                path=(root,),
                exited_modules=frozenset(),
                visited=visited,
                violations=violations,
            )
        return self.dedupe(violations)

    def roots(self, architecture_map: ArchitectureMap) -> tuple[str, ...]:
        roots = tuple(
            source_id
            for source_id in architecture_map.code_map.source_ids()
            if architecture_map.code_map.incoming_dependencies(FileId(source_id)).count() == 0
        )
        if roots:
            return tuple(sorted(roots))
        return tuple(sorted(architecture_map.code_map.source_ids()))

    def walk_dependencies(
        self,
        architecture_map: ArchitectureMap,
        source_id: str,
        path: tuple[str, ...],
        exited_modules: frozenset[str],
        visited: set[NoReentryTraversalState],
        violations: list[FlowViolation],
    ) -> None:
        state = NoReentryTraversalState(source_id=source_id, exited_modules=exited_modules)
        if state in visited:
            return
        visited.add(state)
        source_module = self.module_for(architecture_map, source_id)
        dependencies = sorted(
            architecture_map.code_map.outgoing_dependencies(FileId(source_id)).all(),
            key=lambda dependency: (
                dependency.edge.to_id or "",
                dependency.edge.specifier,
                dependency.edge.kind,
            ),
        )
        for dependency in dependencies:
            target_id = dependency.edge.to_id
            if target_id is None:
                continue
            target_module = self.module_for(architecture_map, target_id)
            next_exited = exited_modules
            if source_module and target_module and (source_module != target_module):
                next_exited = exited_modules.union((source_module,))
            if target_module and target_module in exited_modules:
                violations.append(
                    FlowViolation(
                        violation_type=self.name,
                        path=(*path, target_id),
                        violation_index=len(path),
                        rule_name=self.rule_name(architecture_map),
                        message="module layer re-entered after exit",
                        source_module=source_module,
                        target_module=target_module,
                    )
                )
                continue
            self.walk_dependencies(
                architecture_map=architecture_map,
                source_id=target_id,
                path=(*path, target_id),
                exited_modules=next_exited,
                visited=visited,
                violations=violations,
            )
