from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.source_member_kind import SourceMemberKind
from ......shared.code.models.source_types.kind import SourceTypeKind
from ......shared.code.models.values.source_class_property import SourceClassProperty
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..classes.classifier import PythonClassClassifier
from ..contribution import PythonSemanticContribution
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..properties.classifier import PythonPropertyClassifier
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="20-property")
@dataclass(frozen=True)
class PropertySemanticContributor(PythonSemanticContributor):
    properties: PythonPropertyClassifier
    classes: PythonClassClassifier
    identities: PythonDeclarationIdentityFactory

    @property
    def order(self) -> int:
        return 20

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        by_class: dict[str, dict[str, SourceClassProperty]] = {}
        for candidate in observation.properties:
            class_candidate = next(item for item in observation.classes if item.node.name == candidate.class_name)
            owner_id = self.identities.create(
                context.source_id,
                self.classes.classify(class_candidate),
                candidate.class_name,
                candidate.class_line,
                candidate.class_column,
            )
            owner = str(owner_id.ordinal)
            if owner not in by_class:
                by_class[owner] = {}
            declaration_id = self.identities.create(
                context.source_id,
                DeclarationFamily.PROPERTY,
                f"{candidate.class_name}.{candidate.name}",
                candidate.statement.lineno,
                candidate.statement.col_offset,
            )
            source_property = self.properties.classify(candidate, declaration_id, owner_id)
            class_properties = by_class[owner]
            if source_property.name in class_properties:
                source_property = self.merge(class_properties[source_property.name], source_property)
            class_properties[source_property.name] = source_property
        return PythonSemanticContribution(
            properties={owner: tuple(items.values()) for owner, items in by_class.items()}
        )

    def merge(self, current: SourceClassProperty, incoming: SourceClassProperty) -> SourceClassProperty:
        member_kind = SourceMemberKind.STATIC
        if SourceMemberKind.INSTANCE in {current.member_kind, incoming.member_kind}:
            member_kind = SourceMemberKind.INSTANCE
        source_type = current.type if current.type.kind is not SourceTypeKind.ABSENT else incoming.type
        return SourceClassProperty(
            declaration_id=current.declaration_id,
            owner_declaration_id=current.owner_declaration_id,
            name=current.name,
            is_optional=current.is_optional or incoming.is_optional,
            type=source_type,
            visibility=current.visibility,
            member_kind=member_kind,
            assigned_values=(*current.assigned_values, *incoming.assigned_values),
        )
