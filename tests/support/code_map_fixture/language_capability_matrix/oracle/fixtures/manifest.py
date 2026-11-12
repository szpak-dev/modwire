from typing import Literal

from ....fixture_model import FixtureModel
from ...values.enums.fixture_reference_kind import FixtureReferenceKind
from ...values.names.manifest_scenario_id import ManifestScenarioId


class ManifestFixtureReference(FixtureModel):
    kind: Literal[FixtureReferenceKind.MANIFEST]
    scenario: ManifestScenarioId
