import abc
from abc import ABC
from collections.abc import Iterable, Iterator

from modwire.architecture.config.models.shape_rules import ShapeRules
from modwire.architecture.shape.models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from modwire.architecture.shape.models.shape_violation import ShapeViolation
from modwire.shared.code.models.source_file_result import SourceFileResult


class ShapeResolverInterface(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def title(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        raise NotImplementedError


class SymbolShapeResolverInterface(ShapeResolverInterface):
    pass


class BaseShapeResolver(ABC):
    def realm_source_ids(self, architecture_map: ShapeRealmArchitectureMap) -> Iterator[str]:
        return (
            source_id
            for source_id in architecture_map.code_map.source_ids()
            if self.source_is_in_realm(architecture_map, source_id)
        )

    def realm_results[RealmResult: SourceFileResult](
        self, architecture_map: ShapeRealmArchitectureMap, results: Iterable[RealmResult]
    ) -> Iterator[RealmResult]:
        return (result for result in results if self.source_is_in_realm(architecture_map, result.source_id))

    def source_is_in_realm(self, architecture_map: ShapeRealmArchitectureMap, source_id: str) -> bool:
        return source_id in architecture_map.shape_realm_source_ids

    def limit_violation(
        self, *, source_id: str, rule_name: str, actual: int, limit: int, symbol_kind: str, symbol_name: str
    ) -> ShapeViolation | None:
        if limit < 0 or actual <= limit:
            return None
        return ShapeViolation(
            source_id=source_id,
            rule_name=rule_name,
            actual=actual,
            limit=limit,
            symbol_kind=symbol_kind,
            symbol_name=symbol_name,
        )
