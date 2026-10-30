from typing import Self

from pydantic import Field, model_validator

from modwire.application import CapabilityStatus, FactCapability, RelationshipFamily

from ....fixture_model import FixtureModel
from ...values.enums.claim_state import ClaimState
from ...values.enums.evidence_role import EvidenceRole
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
        evidence_roles: dict[tuple[FixtureRole, str, str], EvidenceRole] = {}
        for scenario in self.scenarios:
            claims = tuple(claim.root for claim in scenario.claims)
            identities = tuple(claim.model_dump_json(exclude={"evidence"}) for claim in claims)
            if len(set(identities)) != len(identities):
                raise ValueError(f"{scenario.name.value} contains duplicate atomic claims")
            for claim in claims:
                identity = (
                    scenario.fixture,
                    scenario.source.value.as_posix(),
                    claim.model_dump_json(exclude={"evidence"}),
                )
                if identity in evidence_roles and evidence_roles[identity] is not claim.evidence:
                    raise ValueError("the same observation cannot prove both supported and boundary evidence")
                evidence_roles[identity] = claim.evidence
                if claim.kind == "capability":
                    self.validate_capability_observation(claim)
                elif claim.kind == "relationship":
                    self.validate_relationship_observation(claim)
                if claim.state is ClaimState.UNSUPPORTED and (
                    claim.kind != "capability" or claim.observation.root.kind != "type_slot"
                ):
                    raise ValueError("unsupported claim state requires a type-slot observation")
                if claim.kind == "capability" and claim.evidence is EvidenceRole.SUPPORTED:
                    absent_type = (
                        claim.observation.root.kind == "type_slot"
                        and claim.state is ClaimState.ABSENT
                        and self.capabilities[claim.capability].status is CapabilityStatus.SUPPORTED
                    )
                    if claim.state is not ClaimState.PRESENT and not absent_type:
                        raise ValueError("supported evidence must observe a published fact")
                    if self.capabilities[claim.capability].status is CapabilityStatus.UNSUPPORTED:
                        raise ValueError("unsupported capability cannot claim supported evidence")
                if claim.kind == "relationship" and claim.evidence is EvidenceRole.SUPPORTED:
                    if claim.state is not ClaimState.PRESENT:
                        raise ValueError("supported relationship evidence must observe a published fact")
                observation = claim.observation.root
                if observation.kind == "source" and observation.relative_path != scenario.source:
                    raise ValueError(f"{scenario.name.value} source observation differs from its scenario source")
                if observation.kind == "empty_source" and observation.relative_path != scenario.source:
                    raise ValueError(f"{scenario.name.value} source observation differs from its scenario source")
        self.validate_claim_coverage()
        self.validate_fixture_ownership()
        return self

    def validate_capability_observation(self, claim: CapabilityClaim) -> None:
        accepted = {
            FactCapability.SOURCES: {"source", "empty_source"},
            FactCapability.SYMBOLS: {"declaration"},
            FactCapability.CALLABLES: {"callable"},
            FactCapability.CALLS: {"call"},
            FactCapability.PARAMETERS: {"parameter", "parameter_kinds"},
            FactCapability.TYPE_REFERENCES: {"type_reference", "type_slot"},
            FactCapability.ANNOTATIONS: {"annotation"},
            FactCapability.MODIFIERS: {"modifier", "callable", "attribute"},
            FactCapability.ATTRIBUTES: {"attribute"},
            FactCapability.ASSIGNED_VALUES: {"assigned_values"},
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
            RelationshipFamily.DECLARATION: {"declaration_relation"},
            RelationshipFamily.MEMBER: {"attribute", "call", "assigned_values"},
            RelationshipFamily.DEPENDENCY: {"dependency"},
        }
        if claim.observation.root.kind not in accepted[claim.relationship]:
            raise ValueError(f"{claim.relationship.value} claim uses an incompatible observation")

    def validate_claim_coverage(self) -> None:
        capability_claims = {
            (claim.capability, claim.evidence)
            for scenario in self.scenarios
            for wrapped in scenario.claims
            for claim in (wrapped.root,)
            if claim.kind == "capability"
        }
        relationship_claims = {
            (claim.relationship, claim.aspect, claim.evidence)
            for scenario in self.scenarios
            for wrapped in scenario.claims
            for claim in (wrapped.root,)
            if claim.kind == "relationship"
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
        for role, fixture in fixtures.items():
            evidenced = {
                scenario.source.value
                for scenario in self.scenarios
                if scenario.fixture is role
                and any(
                    claim.root.observation.root.kind != "source"
                    and (claim.root.state is ClaimState.PRESENT or claim.root.observation.root.kind == "type_slot")
                    for claim in scenario.claims
                )
            }
            if evidenced != {source.value for source in fixture.sources}:
                raise ValueError(f"{self.language.value} {role.value} sources lack behavioral evidence")
