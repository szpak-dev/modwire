from typing import Self

from pydantic import Field, model_validator

from ..projections.mappings.source import SourceIdentityProjection
from .disposition import ScenarioDisposition
from .fixtures.reference import ScenarioFixtureReference


class ScenarioBindingDocument(ScenarioDisposition):
    fixture: ScenarioFixtureReference
    mappings: tuple[SourceIdentityProjection, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_mappings(self) -> Self:
        authored = tuple(mapping.authored for mapping in self.mappings)
        canonical = tuple(mapping.canonical for mapping in self.mappings)
        if len(set(authored)) != len(authored) or len(set(canonical)) != len(canonical):
            raise ValueError("scenario source mappings must be one-to-one")
        return self
