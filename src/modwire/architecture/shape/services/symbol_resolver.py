from collections.abc import Sequence
from dataclasses import dataclass

from wireup import injectable

from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, ShapeResolverInterface, SymbolShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from ..models.shape_violation import ShapeViolation


@injectable(as_type=ShapeResolverInterface, qualifier="symbol")
@dataclass(frozen=True)
class SymbolResolver(ShapeResolverInterface, BaseShapeResolver):
    resolvers: Sequence[SymbolShapeResolverInterface]

    @property
    def name(self) -> str:
        return "symbol"

    @property
    def title(self) -> str:
        return "Symbol Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        violations: list[ShapeViolation] = []
        for resolver in sorted(self.resolvers, key=lambda resolver: resolver.name):
            violations.extend(resolver.resolve(architecture_map, config))
        return tuple(violations)
