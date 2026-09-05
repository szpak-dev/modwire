from collections.abc import Sequence
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.source_class_property import SourceClassProperty
from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, SymbolShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from ..models.shape_violation import ShapeViolation


@injectable(as_type=SymbolShapeResolverInterface, qualifier="property")
@dataclass(frozen=True)
class PropertyResolver(SymbolShapeResolverInterface, BaseShapeResolver):
    @property
    def name(self) -> str:
        return "property"

    @property
    def title(self) -> str:
        return "Property Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        if config.allow_optional_class_properties:
            return ()
        violations: list[ShapeViolation] = []
        for class_result in self.realm_results(architecture_map, architecture_map.code_map.classes().all()):
            source_class = class_result.item
            violations.extend(
                self.property_violations(
                    source_id=class_result.source_id,
                    symbol_kind="class_property",
                    symbol_name=source_class.name,
                    properties=source_class.properties,
                )
            )
        for interface_result in self.realm_results(architecture_map, architecture_map.code_map.interfaces().all()):
            source_interface = interface_result.item
            violations.extend(
                self.property_violations(
                    source_id=interface_result.source_id,
                    symbol_kind="interface_property",
                    symbol_name=source_interface.name,
                    properties=source_interface.properties,
                )
            )
        for type_result in self.realm_results(architecture_map, architecture_map.code_map.types().all()):
            source_type = type_result.item
            violations.extend(
                self.property_violations(
                    source_id=type_result.source_id,
                    symbol_kind="type_property",
                    symbol_name=source_type.name,
                    properties=source_type.properties,
                )
            )
        for abstract_class_result in self.realm_results(
            architecture_map, architecture_map.code_map.abstract_classes().all()
        ):
            abstract_class = abstract_class_result.item
            violations.extend(
                self.property_violations(
                    source_id=abstract_class_result.source_id,
                    symbol_kind="abstract_class_property",
                    symbol_name=abstract_class.name,
                    properties=abstract_class.properties,
                )
            )
        return tuple(violations)

    def property_violations(
        self, *, source_id: str, symbol_kind: str, symbol_name: str, properties: Sequence[SourceClassProperty]
    ) -> tuple[ShapeViolation, ...]:
        return tuple(
            ShapeViolation(
                source_id=source_id,
                rule_name="allow_optional_class_properties",
                actual=True,
                limit=False,
                symbol_kind=symbol_kind,
                symbol_name=property_.name or symbol_name,
            )
            for property_ in properties
            if property_.is_optional
        )
