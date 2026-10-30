from pydantic import Field

from ....fixture_model import FixtureModel
from ...values.enums.fixture_role import FixtureRole
from ...values.names.scenario_id import ScenarioId
from ...values.paths.source_path import RepositorySourcePath
from .claims.scenario import ScenarioClaim


class CapabilityScenario(FixtureModel):
    name: ScenarioId
    fixture: FixtureRole
    source: RepositorySourcePath
    claims: tuple[ScenarioClaim, ...] = Field(min_length=1)
