from ....model import FixtureModel
from .declaration import DeclarationRelationshipLimitationExpectation
from .dependency import DependencyRelationshipLimitationExpectation
from .member import MemberRelationshipLimitationExpectation


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
