from typing import Annotated

from pydantic import Field

from .....fixture_root_model import FixtureRootModel
from .capability import CapabilityClaim
from .relationship import RelationshipClaim


class ScenarioClaim(FixtureRootModel[Annotated[CapabilityClaim | RelationshipClaim, Field(discriminator="kind")]]):
    pass
