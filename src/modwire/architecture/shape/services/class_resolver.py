from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.declarations.source_symbol import SourceSymbol
from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, SymbolShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from ..models.shape_rule_kind import ShapeRuleKind
from ..models.shape_symbol_kind import ShapeSymbolKind
from ..models.shape_violation import ShapeViolation


@injectable(as_type=SymbolShapeResolverInterface, qualifier="class")
@dataclass(frozen=True)
class ClassResolver(SymbolShapeResolverInterface, BaseShapeResolver):
    @property
    def name(self) -> str:
        return "class"

    @property
    def title(self) -> str:
        return "Class Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        violations: list[ShapeViolation] = []
        for class_result in self.realm_results(architecture_map, architecture_map.code_map.classes().all()):
            violations.extend(
                self.class_violations(
                    source_id=class_result.source_id,
                    symbol_kind=ShapeSymbolKind.CLASS,
                    symbol=class_result.item,
                    method_count=len(class_result.item.methods),
                    config=config,
                )
            )
        for interface_result in self.realm_results(architecture_map, architecture_map.code_map.interfaces().all()):
            violations.extend(
                self.class_violations(
                    source_id=interface_result.source_id,
                    symbol_kind=ShapeSymbolKind.INTERFACE,
                    symbol=interface_result.item,
                    method_count=len(interface_result.item.methods),
                    config=config,
                )
            )
        for type_result in self.realm_results(architecture_map, architecture_map.code_map.types().all()):
            violations.extend(
                self.class_violations(
                    source_id=type_result.source_id,
                    symbol_kind=ShapeSymbolKind.TYPE,
                    symbol=type_result.item,
                    method_count=None,
                    config=config,
                )
            )
        return tuple(violations)

    def class_violations(
        self,
        *,
        source_id: str,
        symbol_kind: ShapeSymbolKind,
        symbol: SourceSymbol,
        method_count: int | None,
        config: ShapeRules,
    ) -> tuple[ShapeViolation, ...]:
        violations = [
            self.limit_violation(
                source_id=source_id,
                rule_name=ShapeRuleKind.MAX_CLASS_LINES,
                actual=symbol.line_count,
                limit=config.max_class_lines,
                symbol_kind=symbol_kind,
                symbol_name=symbol.name,
            )
        ]
        if method_count is not None:
            violations.append(
                self.limit_violation(
                    source_id=source_id,
                    rule_name=ShapeRuleKind.MAX_METHODS_PER_CLASS,
                    actual=method_count,
                    limit=config.max_methods_per_class,
                    symbol_kind=symbol_kind,
                    symbol_name=symbol.name,
                )
            )
        return tuple(violation for violation in violations if violation is not None)
