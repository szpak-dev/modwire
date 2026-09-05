from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.config.models.shape_rules import ShapeRules
from modwire.architecture.shape.domain import BaseShapeResolver, SymbolShapeResolverInterface
from modwire.architecture.shape.models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from modwire.architecture.shape.models.shape_violation import ShapeViolation
from modwire.shared.code.models.source_signature import SourceSignature


@injectable(as_type=SymbolShapeResolverInterface, qualifier="signature")
@dataclass(frozen=True)
class SignatureResolver(SymbolShapeResolverInterface, BaseShapeResolver):
    @property
    def name(self) -> str:
        return "signature"

    @property
    def title(self) -> str:
        return "Signature Shape"

    def resolve(self, architecture_map: ShapeRealmArchitectureMap, config: ShapeRules) -> tuple[ShapeViolation, ...]:
        violations: list[ShapeViolation] = []
        for interface_result in self.realm_results(architecture_map, architecture_map.code_map.interfaces().all()):
            source_interface = interface_result.item
            for signature in source_interface.signatures:
                violations.extend(
                    self.signature_violations(
                        source_id=interface_result.source_id,
                        symbol_name=source_interface.name,
                        signature=signature,
                        config=config,
                    )
                )
        for type_result in self.realm_results(architecture_map, architecture_map.code_map.types().all()):
            source_type = type_result.item
            for signature in source_type.signatures:
                violations.extend(
                    self.signature_violations(
                        source_id=type_result.source_id,
                        symbol_name=source_type.name,
                        signature=signature,
                        config=config,
                    )
                )
        return tuple(violations)

    def signature_violations(
        self, *, source_id: str, symbol_name: str, signature: SourceSignature, config: ShapeRules
    ) -> tuple[ShapeViolation, ...]:
        violations = [
            self.limit_violation(
                source_id=source_id,
                rule_name="max_declared_args",
                actual=signature.declared_args,
                limit=config.max_declared_args,
                symbol_kind="signature",
                symbol_name=symbol_name,
            )
        ]
        if not config.allow_optional_method_args and signature.optional_args:
            violations.append(
                ShapeViolation(
                    source_id=source_id,
                    rule_name="allow_optional_method_args",
                    actual=True,
                    limit=False,
                    symbol_kind="signature",
                    symbol_name=symbol_name,
                )
            )
        return tuple(violation for violation in violations if violation is not None)
