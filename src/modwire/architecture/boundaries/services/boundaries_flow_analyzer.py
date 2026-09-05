from collections.abc import Sequence
from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.boundaries.domain import FlowAnalyzerInterface
from modwire.architecture.boundaries.models.flow_violation import FlowViolation
from modwire.architecture.config.models.boundaries_config import BoundariesConfig
from modwire.architecture.config.models.flow_rules import FlowRules
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.map.models.architecture_realm import ArchitectureRealm


@injectable()
@dataclass(frozen=True)
class BoundariesFlowAnalyzer:
    analyzers: Sequence[FlowAnalyzerInterface]

    @property
    def _analyzers(self) -> dict[str, FlowAnalyzerInterface]:
        return {analyzer.name: analyzer for analyzer in self.analyzers}

    def analyzer_names(self, config: BoundariesConfig) -> tuple[str, ...]:
        configured = config.flow.analyzers or tuple(sorted(self._analyzers))
        if config.rules and "module-boundaries" not in configured:
            return ("module-boundaries", *configured)
        return configured

    def analyze(self, architecture_map: ArchitectureMap, config: BoundariesConfig) -> tuple[FlowViolation, ...]:
        violations: list[FlowViolation] = []
        for analyzer_name in self.analyzer_names(config):
            analyzer = self.analyzer(analyzer_name)
            for realm in self.realms(config.flow):
                violations.extend(analyzer.analyze(architecture_map.with_realm(realm), config))
        unique = {violation.violation_key(): violation for violation in violations}
        return tuple(unique[key] for key in sorted(unique))

    def analyzer(self, name: str) -> FlowAnalyzerInterface:
        try:
            return self._analyzers[name]
        except KeyError as error:
            known = ", ".join(sorted(self._analyzers))
            raise ValueError(f"Unknown flow analyzer {name!r}. Known analyzers: {known}") from error

    def realms(self, flow: FlowRules) -> tuple[ArchitectureRealm, ...]:
        if flow.realms:
            return tuple(
                ArchitectureRealm(
                    name=realm.name, module_tag=realm.module_tag or flow.module_tag, layers=realm.layers or flow.layers
                )
                for realm in flow.realms
            )
        return (ArchitectureRealm(name="", module_tag=flow.module_tag, layers=flow.layers),)
