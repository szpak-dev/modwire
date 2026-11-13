from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declarations.source_visibility import SourceVisibility
from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="100-metric")
@dataclass(frozen=True)
class MetricSemanticContributor(PythonSemanticContributor):
    @property
    def order(self) -> int:
        return 100

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        module_classes = {candidate.ordinal for candidate in observation.classes if candidate.module_level}
        public_classes = sum(
            1
            for declaration in catalog.declarations
            if (
                declaration.declaration_id.ordinal in module_classes
                and declaration.visibility_intent is SourceVisibility.PUBLIC
                and not declaration.name.startswith("_")
            )
        )
        public_functions = sum(
            1
            for function in catalog.functions
            if function.visibility_intent is SourceVisibility.PUBLIC and not function.name.startswith("_")
        )
        return PythonSemanticContribution(
            line_count=len(context.content.splitlines()),
            code_line_count=sum(
                1 for line in context.content.splitlines() if line.strip() and not line.strip().startswith("#")
            ),
            public_symbol_count=public_classes + public_functions,
        )
