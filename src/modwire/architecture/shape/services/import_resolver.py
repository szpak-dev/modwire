from dataclasses import dataclass

from wireup import injectable

from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, ShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
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
                        rule_name="allow_import_aliases",
                        actual=False,
                        limit=False,
                        symbol_kind="import",
                        symbol_name=source_import.normalized_path,
                    )
                )
            if source_import.crossing_type not in allowed_crossing_types:
                violations.append(
                    ShapeViolation(
                        source_id=source_id,
                        rule_name="allowed_import_crossing_types",
                        actual=source_import.crossing_type,
                        limit=",".join(config.allowed_import_crossing_types),
                        symbol_kind="import",
                        symbol_name=source_import.normalized_path,
                    )
                )
            if (
                config.require_joined_imports
                and source_import.crossing_type != "module"
                and (not source_import.uses_joined_import)
            ):
                violations.append(
                    ShapeViolation(
                        source_id=source_id,
                        rule_name="require_joined_imports",
                        actual=True,
                        limit=True,
                        symbol_kind="import",
                        symbol_name=source_import.join_key,
                    )
                )
        return tuple(violations)
