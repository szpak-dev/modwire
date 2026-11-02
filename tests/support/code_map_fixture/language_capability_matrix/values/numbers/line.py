from pydantic import Field

from ....fixture_root_model import FixtureRootModel


class SourceLine(FixtureRootModel[int]):
    root: int = Field(ge=1)
