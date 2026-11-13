from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declarations.source_declaration_relation import SourceDeclarationRelation
from ......shared.code.models.declarations.source_declaration_relation_kind import SourceDeclarationRelationKind
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.expression_reference_reader import PythonExpressionReferenceReader
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="80-declaration-relation")
@dataclass(frozen=True)
class DeclarationRelationSemanticContributor(PythonSemanticContributor):
    references: PythonExpressionReferenceReader

    @property
    def order(self) -> int:
        return 80

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        relations: list[SourceDeclarationRelation] = []
        for candidate in observation.declaration_relations:
            reference = self.references.read(candidate)
            relations.append(
                SourceDeclarationRelation(
                    source_declaration_id=catalog.scope_identities[candidate.source.node],
                    kind=SourceDeclarationRelationKind.EXTENDS,
                    target_reference=reference,
                    target=catalog.resolve(reference, candidate.source.binding_scope),
                )
            )
        return PythonSemanticContribution(declaration_relations=tuple(relations))
