from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.source_declaration_relation import SourceDeclarationRelation
from ......shared.code.models.source_declaration_relation_kind import SourceDeclarationRelationKind
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..classes.classifier import PythonClassClassifier
from ..contribution import PythonSemanticContribution
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..policies.expression_reference_reader import PythonExpressionReferenceReader
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="80-inheritance")
@dataclass(frozen=True)
class InheritanceSemanticContributor(PythonSemanticContributor):
    classes: PythonClassClassifier
    references: PythonExpressionReferenceReader
    identities: PythonDeclarationIdentityFactory

    @property
    def order(self) -> int:
        return 80

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        return PythonSemanticContribution(
            declaration_relations=tuple(
                SourceDeclarationRelation(
                    source_declaration_id=self.identities.create(
                        context.source_id,
                        self.classes.classify(candidate.source),
                        candidate.source.node.name,
                        candidate.source.node.lineno,
                        candidate.source.node.col_offset,
                    ),
                    kind=SourceDeclarationRelationKind.EXTENDS,
                    target_reference=self.references.read(candidate),
                )
                for candidate in observation.inheritance
            )
        )
