from typing import Self

from pydantic import Field, model_validator

from modwire.application import SourceParameterKind

from ...model import FixtureModel


class ParameterKindExpectation(FixtureModel):
    source: str = Field(min_length=1)
    present: tuple[SourceParameterKind, ...]
    not_applicable: tuple[SourceParameterKind, ...]

    @model_validator(mode="after")
    def validate_partition(self) -> Self:
        observed = (*self.present, *self.not_applicable)
        if len(observed) != len(set(observed)):
            raise ValueError("parameter kinds overlap")
        if set(observed) != set(SourceParameterKind):
            raise ValueError("parameter kinds do not cover the public enum")
        return self
