from modwire.application import DeclarationIdentity, SourceDeclarationRelationKind

from ...model import FixtureModel


class EvidenceExpectation(FixtureModel):
    count: int
    variants: tuple[str, ...]


class DependencyEvidence(FixtureModel):
    path: str
    resolution: str


class DeclarationRelationEndpointEvidence(FixtureModel):
    source_declaration_id: DeclarationIdentity
    target_reference: str


class DeclarationRelationEvidence(FixtureModel):
    source_declaration_id: DeclarationIdentity
    relation: SourceDeclarationRelationKind
    target_reference: str
