from pydantic import Field

from ....model import FixtureModel
from ...evidence.endpoint import DeclarationRelationEndpointEvidence
from ...evidence.relation import DeclarationRelationEvidence


class CompositionLimitationExpectation(FixtureModel):
    scenario: str = Field(min_length=1)
    present_relations: tuple[DeclarationRelationEvidence, ...]
    absent_endpoints: tuple[DeclarationRelationEndpointEvidence, ...]
