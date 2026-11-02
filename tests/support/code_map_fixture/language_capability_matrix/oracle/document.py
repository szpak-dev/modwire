from pydantic import Field

from ..projections.mappings.source import SourceIdentityProjection
from .disposition import ScenarioDisposition
from .fixtures.reference import ScenarioFixtureReference


class ScenarioBindingDocument(ScenarioDisposition):
    fixture: ScenarioFixtureReference
    mappings: tuple[SourceIdentityProjection, ...] = Field(min_length=1)
