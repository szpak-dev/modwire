from typing import Literal

from ....fixture_model import FixtureModel
from ...values.enums.fixture_role import FixtureRole


class CapabilityFixtureReference(FixtureModel):
    kind: Literal["capability"]
    role: FixtureRole
