from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ......shared.code.models.source_class_property import SourceClassProperty
from ......shared.code.models.source_member_kind import SourceMemberKind
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
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        by_class: dict[str, dict[str, SourceClassProperty]] = {}
        for candidate in observation.properties:
            owner = str(
                self.identities.create(
                    context.source_id,
                    DeclarationFamily.CLASS,
                    candidate.class_name,
                    candidate.class_line,
                    candidate.class_column,
                ).ordinal
            )
            if owner not in by_class:
                by_class[owner] = {}
            source_property = self.properties.classify(candidate)
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
        return SourceClassProperty(
            name=current.name,
            is_optional=current.is_optional or incoming.is_optional,
            annotation=current.annotation or incoming.annotation,
            visibility=current.visibility,
            member_kind=member_kind,
            assigned_values=(*current.assigned_values, *incoming.assigned_values),
        )
