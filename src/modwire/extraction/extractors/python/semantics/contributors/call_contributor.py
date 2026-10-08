from dataclasses import dataclass

from wireup import injectable

from ...observations.call_candidate import PythonCallCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..calls.classifier import PythonCallTargetClassifier
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="90-call")
@dataclass(frozen=True)
class CallSemanticContributor(PythonSemanticContributor):
    targets: PythonCallTargetClassifier

    @property
    def order(self) -> int:
        return 90

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        by_qualified_name = {item.qualified_name: item.id for item in catalog.callables}
        by_name = {item.name: item.id for item in catalog.callables if item.kind in {"function", "callable_value"}}
        constructors_by_name = {item.owner_name: item.id for item in catalog.callables if item.kind == "constructor"}
        candidates = tuple(
            PythonCallCandidate(
                node=call.node,
                source_qualified_name=call.source_qualified_name,
                owner_name=call.owner_name,
                source_id=context.source_id,
                source_callable_id=by_qualified_name[call.source_qualified_name],
                by_name=by_name,
                by_qualified_name=by_qualified_name,
                constructors_by_name=constructors_by_name,
            )
            for call in observation.calls
        )
        return PythonSemanticContribution(calls=tuple(self.targets.classify(candidate) for candidate in candidates))
