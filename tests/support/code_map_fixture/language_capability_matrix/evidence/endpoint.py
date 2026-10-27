from modwire.application import DeclarationIdentity

from ...model import FixtureModel


class DeclarationRelationEndpointEvidence(FixtureModel):
    source_declaration_id: DeclarationIdentity
    target_reference: str
