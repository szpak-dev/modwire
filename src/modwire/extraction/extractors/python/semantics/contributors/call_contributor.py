from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declaration_identity import DeclarationIdentity
from ......shared.code.models.source_callable_kind import SourceCallableKind
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
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        by_qualified_name: dict[str, list[DeclarationIdentity]] = {}
        by_name: dict[str, list[DeclarationIdentity]] = {}
        constructors_by_name: dict[str, list[DeclarationIdentity]] = {}
        by_ordinal: dict[int, DeclarationIdentity] = {}
        for item in catalog.callables:
            if item.qualified_name not in by_qualified_name:
                by_qualified_name[item.qualified_name] = []
            by_qualified_name[item.qualified_name].append(item.declaration_id)
            if item.kind in {SourceCallableKind.FUNCTION, SourceCallableKind.CALLABLE_VALUE}:
                if item.name not in by_name:
                    by_name[item.name] = []
                by_name[item.name].append(item.declaration_id)
            if item.kind is SourceCallableKind.CONSTRUCTOR:
                if item.owner_name not in constructors_by_name:
                    constructors_by_name[item.owner_name] = []
                constructors_by_name[item.owner_name].append(item.declaration_id)
            by_ordinal[item.declaration_id.ordinal] = item.declaration_id
        candidates = tuple(
            PythonCallCandidate(
                node=call.node,
                reference=self.references.read(call),
                source_qualified_name=call.source_qualified_name,
                owner_name=call.owner_name,
                source_id=context.source_id,
                source_callable_id=by_ordinal[call.source_ordinal],
                by_name=by_name,
                by_qualified_name=by_qualified_name,
                constructors_by_name=constructors_by_name,
            )
            for call in observation.calls
        )
        return PythonSemanticContribution(calls=tuple(self.targets.classify(candidates)))
