from abc import ABC, abstractmethod

from modwire.architecture.boundaries.models.flow_violation import FlowViolation
from modwire.architecture.config.models.boundaries_config import BoundariesConfig
from modwire.architecture.map.models.architecture_map import ArchitectureMap


class FlowAnalyzerInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def analyze(self, architecture_map: ArchitectureMap, config: BoundariesConfig) -> tuple[FlowViolation, ...]:
        raise NotImplementedError

    def rule_name(self, architecture_map: ArchitectureMap) -> str:
        if architecture_map.realm.name:
            return f"analyzer:{architecture_map.realm.name}:{self.name}"
        return f"analyzer:{self.name}"


class BaseFlowAnalyzer(ABC):
    def module_for(self, architecture_map: ArchitectureMap, source_id: str) -> str:
        module_tag = architecture_map.realm.module_tag
        if not module_tag:
            return ""
        match = architecture_map.tag_map.first_match(source_id, (module_tag,))
        if match is None:
            return ""
        return match.captured_path or match.name

    def layer_for(self, architecture_map: ArchitectureMap, source_id: str, layers: tuple[str, ...] | None) -> str:
        layer_names = layers or architecture_map.realm.layers
        if not layer_names:
            return ""
        match = architecture_map.tag_map.first_match(source_id, layer_names)
        if match is None:
            return ""
        return match.name

    def dedupe(self, violations: list[FlowViolation]) -> tuple[FlowViolation, ...]:
        seen: set[tuple[object, ...]] = set()
        result: list[FlowViolation] = []
        for violation in violations:
            key = violation.violation_key()
            if key in seen:
                continue
            seen.add(key)
            result.append(violation)
        return tuple(result)
