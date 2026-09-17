from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.source_abstract_class import SourceAbstractClass
from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, SymbolShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from ..models.shape_violation import ShapeViolation


@injectable(as_type=SymbolShapeResolverInterface, qualifier="abstract_class")
@dataclass(frozen=True)
class AbstractClassResolver(SymbolShapeResolverInterface, BaseShapeResolver):
    @property
    def name(self) -> str:
        return "abstract-class"

    @property
    def title(self) -> str:
        return "Abstract Class Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        violations: list[ShapeViolation] = []
        for abstract_class_result in self.realm_results(
            architecture_map, architecture_map.code_map.abstract_classes().all()
        ):
            violations.extend(
                self.abstract_class_violations(
                    source_id=abstract_class_result.source_id, abstract_class=abstract_class_result.item, config=config
                )
            )
        return tuple(violations)

    def abstract_class_violations(
        self, *, source_id: str, abstract_class: SourceAbstractClass, config: ShapeRules
    ) -> tuple[ShapeViolation, ...]:
        method_count = len(abstract_class.abstract_methods) + len(abstract_class.concrete_methods)
        violations = [
            self.limit_violation(
                source_id=source_id,
                rule_name="max_class_lines",
                actual=abstract_class.line_count,
                limit=config.max_class_lines,
                symbol_kind="abstract_class",
                symbol_name=abstract_class.name,
            ),
            self.limit_violation(
                source_id=source_id,
                rule_name="max_methods_per_class",
                actual=method_count,
                limit=config.max_methods_per_class,
                symbol_kind="abstract_class",
                symbol_name=abstract_class.name,
            ),
        ]
        return tuple(violation for violation in violations if violation is not None)
