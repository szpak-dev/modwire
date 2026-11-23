import ast
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.source_declaration import SourceDeclaration
from ......shared.code.models.declarations.source_symbol_kind import SourceSymbolKind
from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ......shared.code.models.inventories.inventory_coverage import InventoryCoverage
from ......shared.code.models.inventories.inventory_status import InventoryStatus
from ......shared.code.models.inventories.member_inventory_coverage import MemberInventoryCoverage
from ...observations.class_candidate import PythonClassCandidate
from ...observations.inventory_evidence import PythonInventoryEvidence
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="30-class")
@dataclass(frozen=True)
class ClassSemanticContributor(PythonSemanticContributor):
    visibility: PythonVisibilityPolicy

    @property
    def order(self) -> int:
        return 30

    def contribute(
        self, observation: PythonSourceObservation, catalog: PythonSemanticCatalog, context: PythonSourceContext
    ) -> PythonSemanticContribution:
        return PythonSemanticContribution(
            declarations=tuple(self.declaration(candidate, catalog) for candidate in observation.classes)
        )

    def declaration(self, candidate: PythonClassCandidate, catalog: PythonSemanticCatalog) -> SourceDeclaration:
        identity = catalog.scope_identities[candidate.node]
        methods = tuple(item for item in catalog.methods if item.owner_declaration_id == identity)
        abstract = tuple(
            item for item in methods if any(name.rsplit(".", 1)[-1] == "abstractmethod" for name in item.decorators)
        )
        start, end = candidate.source_span
        return SourceDeclaration(
            declaration_id=identity,
            kind=SourceSymbolKind.ABSTRACT_CLASS
            if identity.family is DeclarationFamily.ABSTRACT_CLASS
            else SourceSymbolKind.CLASS,
            name=candidate.node.name,
            visibility=SourceVisibility.PUBLIC,
            visibility_intent=self.visibility.classify(candidate.node.name),
            declaration_annotations=tuple(ast.unparse(item) for item in candidate.node.decorator_list),
            methods=tuple(item for item in methods if item not in abstract),
            abstract_methods=abstract,
            properties=catalog.properties[identity] if identity in catalog.properties else (),
            line_count=end - start + 1,
            placement=catalog.placement(candidate.binding_scope),
            inventory=self.inventory(candidate, catalog.inventory),
        )

    def inventory(self, candidate: PythonClassCandidate, evidence: PythonInventoryEvidence) -> MemberInventoryCoverage:
        methods = tuple(evidence.methods[candidate.node])
        properties = (*evidence.properties[candidate.node], *evidence.unowned_properties)
        method_coverage = InventoryCoverage(
            status=InventoryStatus.INCOMPLETE if methods else InventoryStatus.COMPLETE, limitations=methods
        )
        return MemberInventoryCoverage(
            methods=method_coverage,
            abstract_methods=method_coverage,
            properties=InventoryCoverage(
                status=InventoryStatus.INCOMPLETE if properties else InventoryStatus.COMPLETE, limitations=properties
            ),
            signatures=InventoryCoverage(status=InventoryStatus.NOT_APPLICABLE, limitations=()),
        )
