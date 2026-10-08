from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declaration_family import DeclarationFamily
from ......shared.code.models.source_callable import SourceCallable
from ......shared.code.models.source_function import SourceFunction
from ...observations.function_candidate import PythonFunctionCandidate
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.annotation_reader import PythonAnnotationReader
from ..policies.declaration_identity_factory import PythonDeclarationIdentityFactory
from ..policies.parameter_reader import PythonParameterReader
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="40-function")
@dataclass(frozen=True)
class FunctionSemanticContributor(PythonSemanticContributor):
    visibility: PythonVisibilityPolicy
    identities: PythonDeclarationIdentityFactory
    parameters: PythonParameterReader
    annotations: PythonAnnotationReader

    @property
    def order(self) -> int:
        return 40

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        callables = {
            candidate.node: source_callable
            for candidate, source_callable in zip(observation.callables, catalog.callables, strict=True)
        }
        return PythonSemanticContribution(
            functions=tuple(
                self.source_function(candidate, callables[candidate.node], context)
                for candidate in observation.functions
            )
        )

    def source_function(
        self,
        candidate: PythonFunctionCandidate,
        source_callable: SourceCallable,
        context: PythonSourceContext,
    ) -> SourceFunction:
        return SourceFunction(
            declaration_id=self.identities.create(
                context.source_id,
                DeclarationFamily.FUNCTION,
                candidate.node.name,
                candidate.node.lineno,
                candidate.node.col_offset,
            ),
            name=candidate.node.name,
            visibility="public",
            visibility_intent=self.visibility.classify(candidate.node.name),
            declaration_annotations=[],
            line_count=source_callable.line_count,
            declared_args=source_callable.declared_args,
            optional_args=source_callable.optional_args,
        )
