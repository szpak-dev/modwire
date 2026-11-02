from pydantic import Field

from ...fixture_root_model import FixtureRootModel


class CapabilitySchemaVersion(FixtureRootModel[int]):
    root: int = Field(ge=1, le=1)
