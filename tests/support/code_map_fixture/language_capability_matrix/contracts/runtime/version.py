from pydantic import Field

from ....fixture_model import FixtureModel


class RuntimeVersion(FixtureModel):
    major: int = Field(ge=0)
    minor: int = Field(ge=0)
    patch: int = Field(ge=0)

    def text(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
