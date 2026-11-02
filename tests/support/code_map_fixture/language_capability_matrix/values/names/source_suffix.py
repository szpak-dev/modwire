from pydantic import Field

from ....fixture_root_model import FixtureRootModel


class SourceSuffix(FixtureRootModel[str]):
    root: str = Field(pattern="^\\.[a-z0-9]+$")

    @property
    def value(self) -> str:
        return self.root
