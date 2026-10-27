from pydantic import Field

from ....model import FixtureModel
from ...evidence.endpoint import DeclarationRelationEndpointEvidence
from ...evidence.relation import DeclarationRelationEvidence


class DeclarationRelationshipLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_relations: tuple[DeclarationRelationEvidence, ...]
    present_endpoints: tuple[DeclarationRelationEndpointEvidence, ...]
    absent_endpoints: tuple[DeclarationRelationEndpointEvidence, ...]
