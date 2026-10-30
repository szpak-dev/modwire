from pydantic import Field

from ....fixture_model import FixtureModel
from ...values.names.manifest_scenario_id import ManifestScenarioId
from ...values.paths.source_path import RepositorySourcePath
from .claim import ManifestClaim


class ManifestScenario(FixtureModel):
    name: ManifestScenarioId
    source: RepositorySourcePath
    claims: tuple[ManifestClaim, ...] = Field(min_length=1)
