from typing import Annotated

from pydantic import Field

from ....fixture_root_model import FixtureRootModel
from .capability import CapabilityFixtureReference
from .manifest import ManifestFixtureReference


class ScenarioFixtureReference(
    FixtureRootModel[Annotated[CapabilityFixtureReference | ManifestFixtureReference, Field(discriminator="kind")]]
):
    def __hash__(self) -> int:
        return hash(self.root)
