from pydantic import Field

from ...model import FixtureModel


class ManifestTransitionExpectation(FixtureModel):
    before: str = Field(min_length=1)
    after: str = Field(min_length=1)
