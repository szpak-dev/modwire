from pydantic import Field

from ....fixture_model import FixtureModel
from ...values.enums.manifest_change import ManifestChange
from ...values.names.manifest_scenario_id import ManifestScenarioId


class ManifestTransition(FixtureModel):
    before: ManifestScenarioId
    after: ManifestScenarioId
    changes: tuple[ManifestChange, ...] = Field(min_length=1)
