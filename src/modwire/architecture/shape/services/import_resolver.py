from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.sources.import_crossing_type import ImportCrossingType
from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, ShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from ..models.shape_rule_kind import ShapeRuleKind
from ..models.shape_symbol_kind import ShapeSymbolKind
from ..models.shape_violation import ShapeViolation


@injectable(as_type=ShapeResolverInterface, qualifier="import")
@dataclass(frozen=True)
class ImportResolver(ShapeResolverInterface, BaseShapeResolver):
    @property
    def name(self) -> str:
        return "import"

    @property
    def title(self) -> str:
        return "Import Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        violations: list[ShapeViolation] = []
        allowed_crossing_types = set(config.allowed_import_crossing_types)
        for import_result in self.realm_results(architecture_map, architecture_map.code_map.imports().all()):
            source_id = import_result.source_id
            source_import = import_result.item
            if not config.allow_import_aliases and source_import.is_aliased:
                violations.append(
                    ShapeViolation(
                        source_id=source_id,
                        rule_name=ShapeRuleKind.ALLOW_IMPORT_ALIASES,
                        actual=False,
                        limit=False,
                        symbol_kind=ShapeSymbolKind.IMPORT,
                        symbol_name=source_import.normalized_path,
                    )
                )
            if source_import.crossing_type not in allowed_crossing_types:
                violations.append(
                    ShapeViolation(
                        source_id=source_id,
                        rule_name=ShapeRuleKind.ALLOWED_IMPORT_CROSSING_TYPES,
                        actual=source_import.crossing_type,
                        limit=",".join(config.allowed_import_crossing_types),
                        symbol_kind=ShapeSymbolKind.IMPORT,
                        symbol_name=source_import.normalized_path,
                    )
                )
            if (
                config.require_joined_imports
                and source_import.crossing_type is not ImportCrossingType.MODULE
                and (not source_import.uses_joined_import)
            ):
                violations.append(
                    ShapeViolation(
                        source_id=source_id,
                        rule_name=ShapeRuleKind.REQUIRE_JOINED_IMPORTS,
                        actual=True,
                        limit=True,
                        symbol_kind=ShapeSymbolKind.IMPORT,
                        symbol_name=source_import.join_key,
                    )
                )
        return tuple(violations)
