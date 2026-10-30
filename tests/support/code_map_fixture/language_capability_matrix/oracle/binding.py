from typing import Self

from pydantic import Field, model_validator

from modwire.application import CodeMap, FileId, SourceFile

from ...fixture_model import FixtureModel
from ..contracts.fixtures.source_set import FixtureSourceSet
from ..projections.mappings.source import SourceIdentityProjection
from ..values.names.scenario_id import ScenarioId
from .expectation import ScenarioFactExpectation
from .identities import FixtureSourceIdentities
from .projection import ScenarioProjectionKind


class LanguageScenarioBinding(FixtureModel):
    scenario: ScenarioId
    fixture: FixtureSourceSet
    mappings: tuple[SourceIdentityProjection, ...] = Field(min_length=1)
    expectations: tuple[ScenarioFactExpectation, ...] = Field(min_length=1)
    projection: ScenarioProjectionKind

    def expected_source(self, code_map: CodeMap, authored: FileId) -> SourceFile:
        identities = FixtureSourceIdentities(
            {
                FileId(mapping.canonical.value.as_posix()): FileId(mapping.authored.value.as_posix())
                for mapping in self.mappings
            }
        )
        canonical = next(
            mapping.canonical for mapping in self.mappings if mapping.authored.value.as_posix() == str(authored)
        )
        return identities.source(code_map.extraction.files[FileId(canonical.value.as_posix())])

    @model_validator(mode="after")
    def validate_source_ownership(self) -> Self:
        authored = tuple(mapping.authored for mapping in self.mappings)
        canonical = tuple(mapping.canonical for mapping in self.mappings)
        if len(set(authored)) != len(authored) or len(set(canonical)) != len(canonical):
            raise ValueError("scenario source mappings must be one-to-one")
        if not set(authored) <= set(self.fixture.sources):
            raise ValueError("scenario mappings name sources outside their fixture")
        if self.projection is ScenarioProjectionKind.SOURCE_IDENTITIES and set(authored) != set(self.fixture.sources):
            raise ValueError("native scenario mappings must cover every owned source")
        return self
