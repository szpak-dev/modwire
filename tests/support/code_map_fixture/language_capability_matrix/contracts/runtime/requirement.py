from typing import Self

from pydantic import model_validator

from ....fixture_model import FixtureModel
from ...values.names.runtime_name import RuntimeName
from .package import RuntimePackageRequirement
from .probe import RuntimeVersionProbe
from .version import RuntimeVersion


class RuntimeRequirement(FixtureModel):
    runtime: RuntimeName
    probe: RuntimeVersionProbe
    version: RuntimeVersion
    packages: tuple[RuntimePackageRequirement, ...]

    @model_validator(mode="after")
    def validate_packages(self) -> Self:
        identities = tuple((package.manager, package.name) for package in self.packages)
        if len(set(identities)) != len(identities):
            raise ValueError("runtime package identities contain duplicates")
        if self.packages and self.runtime.value != "ruby":
            raise ValueError("gem packages require the Ruby runtime")
        return self
