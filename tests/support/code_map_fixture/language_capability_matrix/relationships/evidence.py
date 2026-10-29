from ...model import FixtureModel


class RelationshipEvidenceExpectation(FixtureModel):
    count: int
    variants: tuple[str, ...]

