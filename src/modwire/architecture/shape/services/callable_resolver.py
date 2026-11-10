from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.callables.source_callable import SourceCallable
from ....shared.code.models.callables.source_callable_kind import SourceCallableKind
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
        for result in self.realm_results(architecture_map, architecture_map.code_map.callables().all()):
            if result.item.kind is SourceCallableKind.FUNCTION:
                symbol_kind = "function"
                line_limit = config.max_function_lines
                allow_optional_args = config.allow_optional_function_args
            elif result.item.kind in (
                SourceCallableKind.INSTANCE_METHOD,
                SourceCallableKind.TYPE_METHOD,
                SourceCallableKind.STATIC_METHOD,
                SourceCallableKind.CONSTRUCTOR,
            ):
                symbol_kind = "method"
                line_limit = config.max_method_lines
                allow_optional_args = config.allow_optional_method_args
            else:
                continue
            violations.extend(
                self.callable_violations(
                    source_id=result.source_id,
                    symbol_kind=symbol_kind,
                    symbol=result.item,
                    line_limit=line_limit,
                    allow_optional_args=allow_optional_args,
                    config=config,
                )
            )
        return tuple(violations)

    def callable_violations(
        self,
        *,
        source_id: str,
        symbol_kind: str,
        symbol: SourceCallable,
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
                actual=len(symbol.parameters),
                limit=config.max_declared_args,
                symbol_kind=symbol_kind,
                symbol_name=symbol.name,
            ),
        ]
        if not allow_optional_args and any(parameter.has_default for parameter in symbol.parameters):
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
