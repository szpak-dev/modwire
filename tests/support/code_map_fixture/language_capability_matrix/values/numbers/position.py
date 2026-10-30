from pydantic import Field

from ....fixture_root_model import FixtureRootModel


class SourcePosition(FixtureRootModel[int]):
    root: int = Field(ge=0)
