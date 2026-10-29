from typing import Self

from pydantic import Field, model_validator

from ...model import FixtureModel


class ParameterKindExpectation(FixtureModel):
    source: str = Field(min_length=1)
    present: tuple[str, ...]
    not_applicable: tuple[str, ...]

    @model_validator(mode="after")
    def validate_partition(self) -> Self:
        observed = (*self.present, *self.not_applicable)
        if len(observed) != len(set(observed)):
            raise ValueError("parameter kinds overlap")
        return self
