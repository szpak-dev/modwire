from typing import Self

from pydantic import Field, model_validator

from modwire.application import CapabilityStatus, FactCapability, RelationshipFamily

from ....fixture_model import FixtureModel
from ...values.enums.fixture_role import FixtureRole
from ...values.enums.relationship_aspect import RelationshipAspect
from ...values.names.language_id import LanguageId
from ..fixtures.inventory import LanguageFixtureInventory
from ..manifests.contract import ManifestContract
from ..runtime.requirement import RuntimeRequirement
from ..scenarios.capability import CapabilityScenario
from ..scenarios.claims.capability import CapabilityClaim
from ..scenarios.claims.relationship import RelationshipClaim
from .capability import CapabilityExpectation
from .relationship import RelationshipExpectation


class LanguageContract(FixtureModel):
    language: LanguageId
    runtime: RuntimeRequirement
    fixtures: LanguageFixtureInventory
    capabilities: dict[FactCapability, CapabilityExpectation]
    relationships: dict[RelationshipFamily, RelationshipExpectation]
    scenarios: tuple[CapabilityScenario, ...] = Field(min_length=1)
    manifests: ManifestContract

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        if tuple(self.capabilities) != tuple(FactCapability):
            raise ValueError("contract capabilities must follow the complete canonical vocabulary")
        if tuple(self.relationships) != tuple(RelationshipFamily):
            raise ValueError("contract relationships must follow the complete canonical vocabulary")
        names = tuple(scenario.name for scenario in self.scenarios)
        if len(set(names)) != len(names):
            raise ValueError("capability scenario names contain duplicates")
        for scenario in self.scenarios:
            claims = tuple(claim.root for claim in scenario.claims)
            if any((claim == later for position, claim in enumerate(claims) for later in claims[position + 1 :])):
                raise ValueError(f"{scenario.name.value} contains duplicate atomic claims")
            for claim in claims:
                if claim.kind == "capability":
                    self.validate_capability_observation(claim)
                elif claim.kind == "relationship":
                    self.validate_relationship_observation(claim)
        return self

    def validate_capability_observation(self, claim: CapabilityClaim) -> None:
        accepted = {
            FactCapability.SOURCES: {"source"},
            FactCapability.SYMBOLS: {"declaration"},
            FactCapability.CALLABLES: {"callable"},
            FactCapability.CALLS: {"call"},
            FactCapability.PARAMETERS: {"parameter", "parameter_kinds"},
            FactCapability.TYPE_REFERENCES: {"type_reference", "type_slot"},
            FactCapability.ANNOTATIONS: {"annotation"},
            FactCapability.MODIFIERS: {"modifier"},
            FactCapability.ATTRIBUTES: {"attribute"},
            FactCapability.ASSIGNED_VALUES: {"assigned_value_partition"},
            FactCapability.INHERITANCE: {"declaration_relation"},
            FactCapability.NAMESPACES: {"namespace"},
            FactCapability.DECLARATION_KINDS: {"declaration"},
            FactCapability.COMPOSITION: {"declaration_relation"},
            FactCapability.DEPENDENCIES: {"dependency"},
            FactCapability.SPANS: {"exact_span", "span_owner"},
        }
        if claim.observation.root.kind not in accepted[claim.capability]:
            raise ValueError(f"{claim.capability.value} claim uses an incompatible observation")

    def validate_relationship_observation(self, claim: RelationshipClaim) -> None:
        accepted = {
            RelationshipFamily.DECLARATION: "declaration_relation",
            RelationshipFamily.MEMBER: "attribute",
            RelationshipFamily.DEPENDENCY: "dependency",
        }
        if claim.observation.root.kind != accepted[claim.relationship]:
            raise ValueError(f"{claim.relationship.value} claim uses an incompatible observation")

    def validate_claim_coverage(self) -> None:
        capability_claims = {
            claim.capability
            for scenario in self.scenarios
            for wrapped in scenario.claims
            for claim in (wrapped.root,)
            if claim.kind == "capability"
        }
        relationship_claims = {
            (claim.relationship, claim.aspect)
            for scenario in self.scenarios
            for wrapped in scenario.claims
            for claim in (wrapped.root,)
            if claim.kind == "relationship"
        }
        for capability, expectation in self.capabilities.items():
            if expectation.status is not CapabilityStatus.SUPPORTED and capability not in capability_claims:
                raise ValueError(f"{self.language.value} {capability.value} has no executable claim")
        for relationship, expectation in self.relationships.items():
            if (
                expectation.semantics is not CapabilityStatus.SUPPORTED
                and (relationship, RelationshipAspect.SEMANTICS) not in relationship_claims
            ):
                raise ValueError(f"{self.language.value} {relationship.value} semantics has no executable claim")
            if (
                expectation.inventory is not CapabilityStatus.SUPPORTED
                and (relationship, RelationshipAspect.INVENTORY) not in relationship_claims
            ):
                raise ValueError(f"{self.language.value} {relationship.value} inventory has no executable claim")

    def validate_fixture_ownership(self) -> None:
        fixtures = {
            FixtureRole.EXTENSIONS: self.fixtures.extensions,
            FixtureRole.GAPS: self.fixtures.gaps,
            FixtureRole.TYPES: self.fixtures.types,
            FixtureRole.PARAMETERS: self.fixtures.parameters,
        }
        suffixes = {suffix.value for suffix in self.fixtures.source_suffixes}
        observed_suffixes = {source.value.suffix for fixture in fixtures.values() for source in fixture.sources} | {
            scenario.source.value.suffix for scenario in self.manifests.scenarios
        }
        if observed_suffixes != suffixes:
            raise ValueError(
                f"{self.language.value} source suffix inventory differs: "
                f"declared {sorted(suffixes)}, observed {sorted(observed_suffixes)}"
            )
        for scenario in self.scenarios:
            if scenario.source not in fixtures[scenario.fixture].sources:
                raise ValueError(f"{scenario.name.value} source is outside its fixture inventory")
