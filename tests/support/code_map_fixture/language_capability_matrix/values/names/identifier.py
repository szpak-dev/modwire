from pydantic import Field

from ....fixture_root_model import FixtureRootModel


class Identifier(FixtureRootModel[str]):
    root: str = Field(min_length=1)

    @property
    def value(self) -> str:
        return self.root

    def __str__(self) -> str:
        return self.root
