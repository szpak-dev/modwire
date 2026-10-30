from typing import Self

from pydantic import Field, model_validator

from modwire.application import FileId

from ...fixture_model import FixtureModel
from .reference import FixtureFactReference


class CanonicalFixtureScenario(FixtureModel):
    sources: tuple[FileId, ...] = Field(min_length=1)
    facts: tuple[FixtureFactReference, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source_ownership(self) -> Self:
        if len(set(self.sources)) != len(self.sources):
            raise ValueError("canonical scenario sources contain duplicates")
        if len(set(self.facts)) != len(self.facts):
            raise ValueError("canonical scenario fact selectors contain duplicates")
        if {fact.source_id() for fact in self.facts} != set(self.sources):
            raise ValueError("canonical scenario fact selectors do not cover its exact sources")
        return self
