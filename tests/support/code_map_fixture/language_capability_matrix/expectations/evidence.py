from pydantic import Field

from ...model import FixtureModel


class EvidenceExpectation(FixtureModel):
    count: int = Field(ge=0)
    variants: tuple[str, ...]
