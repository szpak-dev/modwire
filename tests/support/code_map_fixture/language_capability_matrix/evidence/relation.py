from modwire.application import DeclarationIdentity, SourceDeclarationRelationKind

from ...model import FixtureModel


class DeclarationRelationEvidence(FixtureModel):
    source_declaration_id: DeclarationIdentity
    relation: SourceDeclarationRelationKind
    target_reference: str
