from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.callables.source_callable_kind import SourceCallableKind
from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.declarations.source_binding_kind import SourceBindingKind
from ......shared.code.models.declarations.source_resolved_target import SourceResolvedTarget
from ......shared.code.models.declarations.source_unresolved_reason import SourceUnresolvedReason
from ......shared.code.models.declarations.source_unresolved_target import SourceUnresolvedTarget
from ...observations.call_candidate import PythonCallCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..calls.classifier import PythonCallTargetClassifier
from ..calls.reference_reader import PythonCallReferenceReader
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="90-call")
@dataclass(frozen=True)
class CallSemanticContributor(PythonSemanticContributor):
    targets: PythonCallTargetClassifier
    references: PythonCallReferenceReader

    @property
    def order(self) -> int:
        return 90

    def contribute(
        self, observation: PythonSourceObservation, catalog: PythonSemanticCatalog, context: PythonSourceContext
    ) -> PythonSemanticContribution:
        callables = {item.declaration_id for item in catalog.canonical_callables()}
        candidates: list[PythonCallCandidate] = []
        for call in observation.calls:
            reference = self.references.read(call)
            target = catalog.resolve(reference.expression, call.binding_scope)
            resolved: list[DeclarationIdentity] = []
            if target.kind is SourceBindingKind.RESOLVED:
                if target.declaration_id in callables:
                    resolved.append(target.declaration_id)
                else:
                    resolved.extend(
                        item.declaration_id
                        for item in catalog.methods
                        if item.owner_declaration_id == target.declaration_id
                        and item.kind is SourceCallableKind.CONSTRUCTOR
                    )
            binding: SourceResolvedTarget | SourceUnresolvedTarget
            if len(resolved) == 1:
                binding = SourceResolvedTarget(declaration_id=resolved[0])
            elif not reference.is_reference:
                binding = SourceUnresolvedTarget(reason=SourceUnresolvedReason.DYNAMIC)
            elif resolved:
                binding = SourceUnresolvedTarget(reason=SourceUnresolvedReason.AMBIGUOUS)
            elif target.kind is SourceBindingKind.UNRESOLVED:
                binding = target
            else:
                binding = SourceUnresolvedTarget(reason=SourceUnresolvedReason.UNOBSERVED)
            candidates.append(
                PythonCallCandidate(
                    node=call.node,
                    reference=reference,
                    ordinal=call.ordinal,
                    source_callable_id=catalog.scope_identities[call.source_callable],
                    target=binding,
                )
            )
        return PythonSemanticContribution(calls=tuple(self.targets.classify(candidates)))
