from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.declarations.declaration_family import DeclarationFamily
from ....shared.code.models.values.source_value_declaration_kind import SourceValueDeclarationKind
from ....shared.code.models.values.source_value_scope import SourceValueScope
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
        for source_result in self.realm_results(architecture_map, code_map.source_files().all()):
            source_id = source_result.source_id
            source_file = source_result.file
            violations.extend(
                [
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_classes_per_file",
                        actual=sum(
                            source_file.declaration_family(item.kind) is DeclarationFamily.CLASS
                            for item in source_file.declarations
                        ),
                        limit=config.max_classes_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_interfaces_per_file",
                        actual=sum(
                            source_file.declaration_family(item.kind) is DeclarationFamily.INTERFACE
                            for item in source_file.declarations
                        ),
                        limit=config.max_interfaces_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_types_per_file",
                        actual=sum(
                            source_file.declaration_family(item.kind) is DeclarationFamily.TYPE
                            for item in source_file.declarations
                        ),
                        limit=config.max_types_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_abstract_classes_per_file",
                        actual=sum(
                            source_file.declaration_family(item.kind) is DeclarationFamily.ABSTRACT_CLASS
                            for item in source_file.declarations
                        ),
                        limit=config.max_abstract_classes_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_functions_per_file",
                        actual=len(source_file.functions),
                        limit=config.max_functions_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                    self.limit_violation(
                        source_id=source_id,
                        rule_name="max_variables_per_file",
                        actual=sum(
                            value.scope is SourceValueScope.MODULE
                            and value.declaration_kind is SourceValueDeclarationKind.ASSIGNMENT
                            for value in source_file.values
                        ),
                        limit=config.max_variables_per_file,
                        symbol_kind="file",
                        symbol_name="",
                    ),
                ]
            )
        return tuple(violation for violation in violations if violation is not None)
