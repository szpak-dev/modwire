import ast
from dataclasses import dataclass
from functools import singledispatchmethod

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_binding_kind import SourceBindingKind
from ......shared.code.models.declarations.source_resolved_target import SourceResolvedTarget
from ......shared.code.models.declarations.source_unresolved_target import SourceUnresolvedTarget
from ......shared.code.models.inventories.inventory_limitation import InventoryLimitation
from ......shared.code.models.inventories.inventory_limitation_kind import InventoryLimitationKind
from ......shared.code.models.inventories.inventory_source_location import InventorySourceLocation
from ......shared.code.models.source_types.kind import SourceTypeKind
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ......shared.code.models.values.source_member_kind import SourceMemberKind
from ...observations.property_candidate import PythonPropertyCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..properties.classifier import PythonPropertyClassifier
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="20-property")
@dataclass(frozen=True)
class PropertySemanticContributor(PythonSemanticContributor):
    properties: PythonPropertyClassifier
    identities: PythonDeclarationIdentityFactory

    @property
    def order(self) -> int:
        return 20

    def contribute(
        self, observation: PythonSourceObservation, catalog: PythonSemanticCatalog, context: PythonSourceContext
    ) -> PythonSemanticContribution:
        by_class: dict[DeclarationIdentity, dict[str, SourceClassProperty]] = {}
        class_ids = {catalog.scope_identities[item.node] for item in observation.classes}
        for candidate in observation.properties:
            if (
                candidate.target in catalog.scope_identities
                and catalog.scope_identities[candidate.target].family is DeclarationFamily.TYPE
            ):
                continue
            owner, kind = self.owner(candidate.target, candidate, catalog)
            if owner.kind is SourceBindingKind.UNRESOLVED or owner.declaration_id not in class_ids:
                start, end = candidate.source_span
                catalog.inventory.unowned_properties.append(
                    InventoryLimitation(
                        kind=InventoryLimitationKind.UNRESOLVED_OWNERSHIP,
                        location=InventorySourceLocation(start_line=start, end_line=end),
                        description=f"Property receiver {ast.unparse(candidate.target)} has no exact source owner.",
                    )
                )
                continue
            owner_id = owner.declaration_id
            if owner_id not in by_class:
                by_class[owner_id] = {}
            identity = self.identities.create(
                context, DeclarationFamily.PROPERTY, f"{owner_id.qualified_name}.{candidate.name}", candidate.ordinal
            )
            incoming = self.properties.classify(
                candidate, identity, owner_id, kind, catalog.placement(candidate.binding_scope)
            )
            properties = by_class[owner_id]
            properties[candidate.name] = (
                self.merge(properties[candidate.name], incoming) if candidate.name in properties else incoming
            )
        return PythonSemanticContribution(
            properties={owner: tuple(items.values()) for owner, items in by_class.items()}
        )

    @singledispatchmethod
    def owner(
        self, target: ast.AST, candidate: PythonPropertyCandidate, catalog: PythonSemanticCatalog
    ) -> tuple[SourceResolvedTarget | SourceUnresolvedTarget, SourceMemberKind]:
        return (
            SourceResolvedTarget(declaration_id=catalog.scope_identities[candidate.binding_scope]),
            SourceMemberKind.INSTANCE,
        )

    @owner.register
    def named_owner(
        self, target: ast.Name, candidate: PythonPropertyCandidate, catalog: PythonSemanticCatalog
    ) -> tuple[SourceResolvedTarget | SourceUnresolvedTarget, SourceMemberKind]:
        return (
            SourceResolvedTarget(declaration_id=catalog.scope_identities[candidate.binding_scope]),
            self.class_member_kind(candidate.statement),
        )

    @owner.register
    def attribute_owner(
        self, target: ast.Attribute, candidate: PythonPropertyCandidate, catalog: PythonSemanticCatalog
    ) -> tuple[SourceResolvedTarget | SourceUnresolvedTarget, SourceMemberKind]:
        receiver = ast.unparse(target.value)
        scope = candidate.binding_scope
        if scope in catalog.callable_kinds and receiver == catalog.receiver_name(scope):
            kind = catalog.callable_kinds[scope]
            if kind in {
                SourceCallableKind.INSTANCE_METHOD,
                SourceCallableKind.CONSTRUCTOR,
                SourceCallableKind.TYPE_METHOD,
            }:
                return (
                    catalog.resolve(receiver, scope),
                    SourceMemberKind.STATIC if kind is SourceCallableKind.TYPE_METHOD else SourceMemberKind.INSTANCE,
                )
        return (catalog.resolve(receiver, scope), SourceMemberKind.STATIC)

    @singledispatchmethod
    def class_member_kind(self, statement: ast.stmt) -> SourceMemberKind:
        return SourceMemberKind.STATIC

    @class_member_kind.register
    def annotated_member_kind(self, statement: ast.AnnAssign) -> SourceMemberKind:
        annotation = ast.unparse(statement.annotation).split("[", 1)[0].rsplit(".", 1)[-1]
        return SourceMemberKind.STATIC if annotation == "ClassVar" else SourceMemberKind.INSTANCE

    def merge(self, current: SourceClassProperty, incoming: SourceClassProperty) -> SourceClassProperty:
        return SourceClassProperty(
            declaration_id=current.declaration_id,
            owner_declaration_id=current.owner_declaration_id,
            name=current.name,
            is_optional=current.is_optional or incoming.is_optional,
            type=current.type if current.type.kind is not SourceTypeKind.ABSENT else incoming.type,
            visibility=current.visibility,
            member_kind=SourceMemberKind.INSTANCE
            if SourceMemberKind.INSTANCE in {current.member_kind, incoming.member_kind}
            else SourceMemberKind.STATIC,
            assigned_values=(*current.assigned_values, *incoming.assigned_values),
            placement=current.placement,
        )
