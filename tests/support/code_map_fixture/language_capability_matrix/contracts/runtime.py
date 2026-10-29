from pydantic import Field

from ...model import FixtureModel
from ..values import ExecutableName, PackageName, RuntimeKind, RuntimePackageManager


class RuntimeVersion(FixtureModel):
    major: int = Field(ge=0)
    minor: int = Field(ge=0)
    patch: int = Field(ge=0)

    def text(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class RuntimePackageRequirement(FixtureModel):
    manager: RuntimePackageManager
    name: PackageName
    version: RuntimeVersion


class RuntimeRequirement(FixtureModel):
    runtime: RuntimeKind
    executable: ExecutableName
    version: RuntimeVersion
    packages: tuple[RuntimePackageRequirement, ...]
