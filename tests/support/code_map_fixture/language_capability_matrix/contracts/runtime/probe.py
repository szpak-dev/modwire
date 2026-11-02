import re
from typing import Self

from pydantic import Field, model_validator

from ....fixture_model import FixtureModel


class RuntimeVersionProbe(FixtureModel):
    arguments: tuple[str, ...] = Field(min_length=1)
    pattern: re.Pattern[str]

    @model_validator(mode="after")
    def validate_version_capture(self) -> Self:
        if self.pattern.groups != 1 or not self.pattern.pattern.startswith("^"):
            raise ValueError("runtime probe requires an anchored identity and one version capture")
        return self
