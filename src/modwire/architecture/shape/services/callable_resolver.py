from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.source_callable_symbol import SourceCallableSymbol
from ...config.models.shape_rules import ShapeRules
from ..domain import BaseShapeResolver, SymbolShapeResolverInterface
from ..models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from ..models.shape_violation import ShapeViolation


@injectable(as_type=SymbolShapeResolverInterface, qualifier="callable")
@dataclass(frozen=True)
class CallableResolver(SymbolShapeResolverInterface, BaseShapeResolver):
    @property
    def name(self) -> str:
        return "callable"

    @property
    def title(self) -> str:
        return "Callable Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        violations: list[ShapeViolation] = []
        for function_result in self.realm_results(architecture_map, architecture_map.code_map.functions().all()):
            violations.extend(
                self.callable_violations(
                    source_id=function_result.source_id,
                    symbol_kind="function",
                    symbol=function_result.item,
                    line_limit=config.max_function_lines,
                    allow_optional_args=config.allow_optional_function_args,
                    config=config,
                )
            )
        for class_result in self.realm_results(architecture_map, architecture_map.code_map.classes().all()):
            for method in class_result.item.methods:
                violations.extend(
                    self.callable_violations(
                        source_id=class_result.source_id,
                        symbol_kind="method",
                        symbol=method,
                        line_limit=config.max_method_lines,
                        allow_optional_args=config.allow_optional_method_args,
                        config=config,
                    )
                )
        for interface_result in self.realm_results(architecture_map, architecture_map.code_map.interfaces().all()):
            for method in interface_result.item.methods:
                violations.extend(
                    self.callable_violations(
                        source_id=interface_result.source_id,
                        symbol_kind="method",
                        symbol=method,
                        line_limit=config.max_method_lines,
                        allow_optional_args=config.allow_optional_method_args,
                        config=config,
                    )
                )
        for abstract_class_result in self.realm_results(
            architecture_map, architecture_map.code_map.abstract_classes().all()
        ):
            abstract_class = abstract_class_result.item
            for method in (*abstract_class.abstract_methods, *abstract_class.concrete_methods):
                violations.extend(
                    self.callable_violations(
                        source_id=abstract_class_result.source_id,
                        symbol_kind="method",
                        symbol=method,
                        line_limit=config.max_method_lines,
                        allow_optional_args=config.allow_optional_method_args,
                        config=config,
                    )
                )
        return tuple(violations)

    def callable_violations(
        self,
        *,
        source_id: str,
        symbol_kind: str,
        symbol: SourceCallableSymbol,
        line_limit: int,
        allow_optional_args: bool,
        config: ShapeRules,
    ) -> tuple[ShapeViolation, ...]:
        line_rule = "max_function_lines" if symbol_kind == "function" else "max_method_lines"
        violations = [
            self.limit_violation(
                source_id=source_id,
                rule_name=line_rule,
                actual=symbol.line_count,
                limit=line_limit,
                symbol_kind=symbol_kind,
                symbol_name=symbol.name,
            ),
            self.limit_violation(
                source_id=source_id,
                rule_name="max_declared_args",
                actual=symbol.declared_args,
                limit=config.max_declared_args,
                symbol_kind=symbol_kind,
                symbol_name=symbol.name,
            ),
        ]
        if not allow_optional_args and symbol.optional_args:
            violations.append(
                ShapeViolation(
                    source_id=source_id,
                    rule_name="allow_optional_function_args"
                    if symbol_kind == "function"
                    else "allow_optional_method_args",
                    actual=True,
                    limit=False,
                    symbol_kind=symbol_kind,
                    symbol_name=symbol.name,
                )
            )
        return tuple(violation for violation in violations if violation is not None)
