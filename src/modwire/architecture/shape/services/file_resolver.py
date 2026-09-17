from dataclasses import dataclass

from wireup import injectable

from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, ShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from ..models.shape_violation import ShapeViolation


@injectable(as_type=ShapeResolverInterface, qualifier="file")
@dataclass(frozen=True)
class FileResolver(ShapeResolverInterface, BaseShapeResolver):
    @property
    def name(self) -> str:
        return "file"

    @property
    def title(self) -> str:
        return "File Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        violations: list[ShapeViolation | None] = []
        code_map = architecture_map.code_map
        for source_id in self.realm_source_ids(architecture_map):
            violations.extend(
                [
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_classes_per_file",
                        actual=code_map.classes().where_equal(lambda result: result.source_id, source_id).count(),
                        limit=config.max_classes_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_interfaces_per_file",
                        actual=code_map.interfaces().where_equal(lambda result: result.source_id, source_id).count(),
                        limit=config.max_interfaces_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_types_per_file",
                        actual=code_map.types().where_equal(lambda result: result.source_id, source_id).count(),
                        limit=config.max_types_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_abstract_classes_per_file",
                        actual=code_map.abstract_classes()
                        .where_equal(lambda result: result.source_id, source_id)
                        .count(),
                        limit=config.max_abstract_classes_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_functions_per_file",
                        actual=code_map.functions().where_equal(lambda result: result.source_id, source_id).count(),
                        limit=config.max_functions_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                ]
            )
        return tuple(violation for violation in violations if violation is not None)
