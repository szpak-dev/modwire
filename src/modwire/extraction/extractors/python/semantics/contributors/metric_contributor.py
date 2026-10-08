from dataclasses import dataclass

from wireup import injectable

from ...observations.source_context import PythonSourceContext
from ...observations.source_observation import PythonSourceObservation
from ..catalog import PythonSemanticCatalog
from ..contribution import PythonSemanticContribution
from ..policies.visibility_policy import PythonVisibilityPolicy
from ..reader import PythonSemanticContributor


@injectable(as_type=PythonSemanticContributor, qualifier="100-metric")
@dataclass(frozen=True)
class MetricSemanticContributor(PythonSemanticContributor):
    visibility: PythonVisibilityPolicy

    @property
    def order(self) -> int:
        return 100

    def contribute(
        self,
        observation: PythonSourceObservation,
        catalog: PythonSemanticCatalog,
        context: PythonSourceContext,
    ) -> PythonSemanticContribution:
        public_classes = sum(
            1
            for candidate in observation.classes
            if (
                candidate.module_level
                and self.visibility.classify(candidate.node.name) == "public"
                and not candidate.node.name.startswith("_")
            )
        )
        public_functions = sum(
            1
            for candidate in observation.functions
            if self.visibility.classify(candidate.node.name) == "public" and not candidate.node.name.startswith("_")
        )
        return PythonSemanticContribution(
            line_count=len(context.content.splitlines()),
            code_line_count=sum(
                1 for line in context.content.splitlines() if line.strip() and not line.strip().startswith("#")
            ),
            public_symbol_count=public_classes + public_functions,
        )
