from ....model import FixtureModel
from .annotation import AnnotationLimitationExpectation
from .attribute import AttributeLimitationExpectation
from .call import CallLimitationExpectation
from .callable import CallableLimitationExpectation
from .composition import CompositionLimitationExpectation
from .dependency import DependencyLimitationExpectation
from .modifier import ModifierLimitationExpectation
from .namespace import NamespaceLimitationExpectation
from .parameter import ParameterLimitationExpectation
from .span import SpanLimitationExpectation
from .symbol import SymbolLimitationExpectation
from .value import AssignedValueLimitationExpectation


class LanguageCapabilityLimitations(FixtureModel):
    symbols: tuple[SymbolLimitationExpectation, ...]
    callables: tuple[CallableLimitationExpectation, ...]
    calls: tuple[CallLimitationExpectation, ...]
    parameters: tuple[ParameterLimitationExpectation, ...]
    annotations: tuple[AnnotationLimitationExpectation, ...]
    modifiers: tuple[ModifierLimitationExpectation, ...]
    attributes: tuple[AttributeLimitationExpectation, ...]
    assigned_values: tuple[AssignedValueLimitationExpectation, ...]
    namespaces: tuple[NamespaceLimitationExpectation, ...]
    composition: tuple[CompositionLimitationExpectation, ...]
    dependencies: tuple[DependencyLimitationExpectation, ...]
    spans: tuple[SpanLimitationExpectation, ...]

    def cases(self) -> tuple[tuple[str, str], ...]:
        return (
            *((limitation.scenario, "symbols") for limitation in self.symbols),
            *((limitation.scenario, "callables") for limitation in self.callables),
            *((limitation.scenario, "calls") for limitation in self.calls),
            *((limitation.scenario, "parameters") for limitation in self.parameters),
            *((limitation.scenario, "annotations") for limitation in self.annotations),
            *((limitation.scenario, "modifiers") for limitation in self.modifiers),
            *((limitation.scenario, "attributes") for limitation in self.attributes),
            *((limitation.scenario, "assigned_values") for limitation in self.assigned_values),
            *((limitation.scenario, "namespaces") for limitation in self.namespaces),
            *((limitation.scenario, "composition") for limitation in self.composition),
            *((limitation.scenario, "dependencies") for limitation in self.dependencies),
            *((limitation.scenario, "spans") for limitation in self.spans),
        )
