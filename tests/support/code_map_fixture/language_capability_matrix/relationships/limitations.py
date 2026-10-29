from pydantic import Field

from modwire.application import SourceAssignedValueKind

from ...model import FixtureModel
from ..capabilities.evidence import (
    DeclarationRelationEndpointEvidence,
    DeclarationRelationEvidence,
    DependencyEvidence,
)


class DeclarationRelationshipLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_relations: tuple[DeclarationRelationEvidence, ...]
    present_endpoints: tuple[DeclarationRelationEndpointEvidence, ...]
    absent_endpoints: tuple[DeclarationRelationEndpointEvidence, ...]


class DependencyRelationshipLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_dependencies: tuple[DependencyEvidence, ...]
    absent_dependencies: tuple[DependencyEvidence, ...]


class MemberRelationshipLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_attribute_names: tuple[str, ...]
    absent_attribute_names: tuple[str, ...]
    present_value_kinds: tuple[SourceAssignedValueKind, ...]
    absent_value_kinds: tuple[SourceAssignedValueKind, ...]


class LanguageRelationshipLimitations(FixtureModel):
    declaration_semantics: tuple[DeclarationRelationshipLimitationExpectation, ...]
    declaration_inventory: tuple[DeclarationRelationshipLimitationExpectation, ...]
    member_semantics: tuple[MemberRelationshipLimitationExpectation, ...]
    member_inventory: tuple[MemberRelationshipLimitationExpectation, ...]
    dependency_semantics: tuple[DependencyRelationshipLimitationExpectation, ...]
    dependency_inventory: tuple[DependencyRelationshipLimitationExpectation, ...]

    def cases(self) -> tuple[tuple[str, str], ...]:
        return (
            *((limitation.scenario, "declaration_semantics") for limitation in self.declaration_semantics),
            *((limitation.scenario, "declaration_inventory") for limitation in self.declaration_inventory),
            *((limitation.scenario, "member_semantics") for limitation in self.member_semantics),
            *((limitation.scenario, "member_inventory") for limitation in self.member_inventory),
            *((limitation.scenario, "dependency_semantics") for limitation in self.dependency_semantics),
            *((limitation.scenario, "dependency_inventory") for limitation in self.dependency_inventory),
        )
