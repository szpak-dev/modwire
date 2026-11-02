from pydantic import Field

from ...fixture_model import FixtureModel
from ..projections.mappings.source import SourceIdentityProjection
from ..values.names.scenario_id import ScenarioId
from .fixtures.reference import ScenarioFixtureReference


class ScenarioBindingDocument(FixtureModel):
    scenario: ScenarioId
    fixture: ScenarioFixtureReference
    mappings: tuple[SourceIdentityProjection, ...] = Field(min_length=1)
