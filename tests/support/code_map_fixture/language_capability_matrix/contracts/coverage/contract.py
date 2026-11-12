from typing import Self

from pydantic import Field, model_validator

from modwire.application import CapabilityStatus, FactCapability, RelationshipFamily

from ....fixture_model import FixtureModel
from ...values.enums.claim_kind import ClaimKind
from ...values.enums.claim_state import ClaimState
from ...values.enums.evidence_role import EvidenceRole
from ...values.enums.fixture_role import FixtureRole
from ...values.enums.observation_kind import ObservationKind
from ...values.enums.relationship_aspect import RelationshipAspect
from ...values.names.language_id import LanguageId
from ...values.paths.source_path import RepositorySourcePath
from ..fixtures.inventory import LanguageFixtureInventory
from ..manifests.contract import ManifestContract
from ..runtime.requirement import RuntimeRequirement
from ..scenarios.capability import CapabilityScenario
from ..scenarios.claims.capability import CapabilityClaim
from ..scenarios.claims.relationship import RelationshipClaim
from ..scenarios.claims.scenario import ScenarioClaim
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
        owned_claims: list[tuple[FixtureRole, RepositorySourcePath, ScenarioClaim]] = []
        for scenario in self.scenarios:
            for wrapped in scenario.claims:
                if any(
                    role is scenario.fixture and source == scenario.source and wrapped.same_fact(previous)
                    for role, source, previous in owned_claims
                ):
                    raise ValueError("atomic fixture claims must have exactly one scenario owner and evidence role")
                owned_claims.append((scenario.fixture, scenario.source, wrapped))
                claim = wrapped.root
                if claim.kind is ClaimKind.CAPABILITY:
                    self.validate_capability_observation(claim)
                elif claim.kind is ClaimKind.RELATIONSHIP:
                    self.validate_relationship_observation(claim)
                if claim.state is ClaimState.UNSUPPORTED and (
                    claim.kind is not ClaimKind.CAPABILITY
                    or claim.observation.root.kind is not ObservationKind.TYPE_SLOT
                ):
                    raise ValueError("unsupported claim state requires a type-slot observation")
                if claim.kind is ClaimKind.CAPABILITY and claim.evidence is EvidenceRole.SUPPORTED:
                    absent_type = (
                        claim.observation.root.kind is ObservationKind.TYPE_SLOT
                        and claim.state is ClaimState.ABSENT
                        and self.capabilities[claim.capability].status is CapabilityStatus.SUPPORTED
                    )
                    if claim.state is not ClaimState.PRESENT and not absent_type:
                        raise ValueError("supported evidence must observe a published fact")
                    if self.capabilities[claim.capability].status is CapabilityStatus.UNSUPPORTED:
                        raise ValueError("unsupported capability cannot claim supported evidence")
                if claim.kind is ClaimKind.RELATIONSHIP and claim.evidence is EvidenceRole.SUPPORTED:
                    if claim.state is not ClaimState.PRESENT:
                        raise ValueError("supported relationship evidence must observe a published fact")
                    expectation = self.relationships[claim.relationship]
                    status = (
                        expectation.semantics if claim.aspect is RelationshipAspect.SEMANTICS else expectation.inventory
                    )
                    if status is CapabilityStatus.UNSUPPORTED:
                        raise ValueError("unsupported relationship aspect cannot claim supported evidence")
                observation = claim.observation.root
                if observation.kind is ObservationKind.SOURCE and observation.relative_path != scenario.source:
                    raise ValueError(f"{scenario.name.value} source observation differs from its scenario source")
                if observation.kind is ObservationKind.EMPTY_SOURCE and observation.relative_path != scenario.source:
                    raise ValueError(f"{scenario.name.value} source observation differs from its scenario source")
        self.validate_claim_coverage()
        self.validate_fixture_ownership()
        return self

    def validate_capability_observation(self, claim: CapabilityClaim) -> None:
        accepted = {
            FactCapability.SOURCES: {ObservationKind.SOURCE, ObservationKind.EMPTY_SOURCE},
            FactCapability.SYMBOLS: {ObservationKind.DECLARATION},
            FactCapability.CALLABLES: {ObservationKind.CALLABLE},
            FactCapability.CALLS: {ObservationKind.CALL},
            FactCapability.PARAMETERS: {ObservationKind.PARAMETER, ObservationKind.PARAMETER_LIST},
            FactCapability.TYPE_REFERENCES: {ObservationKind.TYPE_REFERENCE, ObservationKind.TYPE_SLOT},
            FactCapability.ANNOTATIONS: {ObservationKind.ANNOTATION},
            FactCapability.MODIFIERS: {ObservationKind.MODIFIER, ObservationKind.CALLABLE, ObservationKind.ATTRIBUTE},
            FactCapability.ATTRIBUTES: {ObservationKind.ATTRIBUTE},
            FactCapability.ASSIGNED_VALUES: {ObservationKind.ASSIGNED_VALUES},
            FactCapability.INHERITANCE: {ObservationKind.DECLARATION_RELATION},
            FactCapability.NAMESPACES: {ObservationKind.NAMESPACE},
            FactCapability.DECLARATION_KINDS: {ObservationKind.DECLARATION},
            FactCapability.COMPOSITION: {ObservationKind.DECLARATION_RELATION},
            FactCapability.DEPENDENCIES: {ObservationKind.DEPENDENCY},
            FactCapability.SPANS: {ObservationKind.EXACT_SPAN, ObservationKind.SPAN_OWNER},
        }
        if claim.observation.root.kind not in accepted[claim.capability]:
            raise ValueError(f"{claim.capability.value} claim uses an incompatible observation")

    def validate_relationship_observation(self, claim: RelationshipClaim) -> None:
        accepted = {
            RelationshipFamily.DECLARATION: {ObservationKind.DECLARATION_RELATION},
            RelationshipFamily.MEMBER: {
                ObservationKind.ATTRIBUTE,
                ObservationKind.CALL,
                ObservationKind.ASSIGNED_VALUES,
            },
            RelationshipFamily.DEPENDENCY: {ObservationKind.DEPENDENCY},
        }
        if claim.observation.root.kind not in accepted[claim.relationship]:
            raise ValueError(f"{claim.relationship.value} claim uses an incompatible observation")

    def validate_claim_coverage(self) -> None:
        capability_claims = {
            (claim.capability, claim.evidence)
            for scenario in self.scenarios
            for wrapped in scenario.claims
            for claim in (wrapped.root,)
            if claim.kind is ClaimKind.CAPABILITY
        }
        relationship_claims = {
            (claim.relationship, claim.aspect, claim.evidence)
            for scenario in self.scenarios
            for wrapped in scenario.claims
            for claim in (wrapped.root,)
            if claim.kind is ClaimKind.RELATIONSHIP
        }
        obligations = {
            CapabilityStatus.SUPPORTED: {EvidenceRole.SUPPORTED},
            CapabilityStatus.PARTIAL: {EvidenceRole.SUPPORTED, EvidenceRole.BOUNDARY},
            CapabilityStatus.UNSUPPORTED: {EvidenceRole.BOUNDARY},
        }
        for capability, expectation in self.capabilities.items():
            for role in obligations[expectation.status]:
                if (capability, role) not in capability_claims:
                    raise ValueError(f"{self.language.value} {capability.value} lacks {role.value} evidence")
        for relationship, expectation in self.relationships.items():
            for aspect, status in (
                (RelationshipAspect.SEMANTICS, expectation.semantics),
                (RelationshipAspect.INVENTORY, expectation.inventory),
            ):
                for role in obligations[status]:
                    if (relationship, aspect, role) not in relationship_claims:
                        raise ValueError(
                            f"{self.language.value} {relationship.value} {aspect.value} lacks {role.value} evidence"
                        )

    def validate_fixture_ownership(self) -> None:
        fixtures = self.fixtures.source_sets()
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
