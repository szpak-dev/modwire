from typing import Literal

from ....fixture_model import FixtureModel
from ...values.names.manifest_scenario_id import ManifestScenarioId


class ManifestFixtureReference(FixtureModel):
    kind: Literal["manifest"]
    scenario: ManifestScenarioId
