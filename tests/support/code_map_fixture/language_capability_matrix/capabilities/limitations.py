from pydantic import Field

from modwire.application import DeclarationIdentity, SourceAssignedValueKind, SourceMemberKind

from ...model import FixtureModel
from .evidence import DeclarationRelationEndpointEvidence, DeclarationRelationEvidence, DependencyEvidence


class AnnotationLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_annotations: tuple[str, ...]
    absent_annotations: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]


class AttributeLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_attribute_names: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]


class CallLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_resolutions: tuple[str, ...]
    absent_target_names: tuple[str, ...]


class CallableLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_callable_names: tuple[str, ...]
    absent_callable_names: tuple[str, ...]


class CompositionLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_relations: tuple[DeclarationRelationEvidence, ...]
    absent_endpoints: tuple[DeclarationRelationEndpointEvidence, ...]


class DependencyLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_dependencies: tuple[DependencyEvidence, ...]
    absent_dependencies: tuple[DependencyEvidence, ...]


class ModifierLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_visibility_intents: tuple[str, ...]
    present_callable_kinds: tuple[str, ...]
    present_member_kinds: tuple[SourceMemberKind, ...]
    unrepresented_authored_modifiers: tuple[str, ...]


class NamespaceLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    absent_namespaces: tuple[str, ...]


class ParameterLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_parameter_kinds: tuple[str, ...]
    unrepresented_authored_parameters: tuple[str, ...]


class SpanLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_exact_span_owners: tuple[DeclarationIdentity, ...]
    absent_exact_span_owners: tuple[DeclarationIdentity, ...]


class SymbolLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_declaration_names: tuple[str, ...]
    absent_declaration_names: tuple[str, ...]


class TypeReferenceLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_reference_names: tuple[str, ...]
    present_nested_reference_names: tuple[str, ...]
    absent_slot_count: int = Field(ge=0)
    unsupported_slot_count: int = Field(ge=0)


class AssignedValueLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_attribute_names: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]
    expected_value_kinds: dict[str, tuple[SourceAssignedValueKind, ...]]


class LanguageCapabilityLimitations(FixtureModel):
    symbols: tuple[SymbolLimitationExpectation, ...]
    callables: tuple[CallableLimitationExpectation, ...]
    calls: tuple[CallLimitationExpectation, ...]
    parameters: tuple[ParameterLimitationExpectation, ...]
    type_references: tuple[TypeReferenceLimitationExpectation, ...]
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
            *((limitation.scenario, "type_references") for limitation in self.type_references),
            *((limitation.scenario, "annotations") for limitation in self.annotations),
            *((limitation.scenario, "modifiers") for limitation in self.modifiers),
            *((limitation.scenario, "attributes") for limitation in self.attributes),
            *((limitation.scenario, "assigned_values") for limitation in self.assigned_values),
            *((limitation.scenario, "namespaces") for limitation in self.namespaces),
            *((limitation.scenario, "composition") for limitation in self.composition),
            *((limitation.scenario, "dependencies") for limitation in self.dependencies),
            *((limitation.scenario, "spans") for limitation in self.spans),
        )
