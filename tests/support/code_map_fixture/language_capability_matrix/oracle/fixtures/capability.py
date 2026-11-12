from typing import Literal

from ....fixture_model import FixtureModel
from ...values.enums.fixture_reference_kind import FixtureReferenceKind
from ...values.enums.fixture_role import FixtureRole


class CapabilityFixtureReference(FixtureModel):
    kind: Literal[FixtureReferenceKind.CAPABILITY]
    role: FixtureRole
