from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import Field, model_validator

from ..model import FixtureRootModel


class RepositoryPath(FixtureRootModel[PurePosixPath]):
    @property
    def value(self) -> PurePosixPath:
        return self.root

    @model_validator(mode="after")
    def validate_relative(self) -> Self:
        if self.value.is_absolute() or ".." in self.value.parts:
            raise ValueError("repository paths must be normalized relative paths")
        return self


class RepositorySourcePath(RepositoryPath):
    pass


class RepositoryDocumentPath(RepositoryPath):
    pass


class Identifier(FixtureRootModel[str]):
    root: str = Field(min_length=1)

    @property
    def value(self) -> str:
        return self.root


class QualifiedName(Identifier):
    pass


class AnnotationExpression(Identifier):
    pass


class AuthoredModifier(Identifier):
    pass


class LanguageId(Identifier):
    pass


class ScenarioId(Identifier):
    pass


class ManifestScenarioId(ScenarioId):
    pass


class CapabilityExplanation(Identifier):
    pass


class ExecutableName(Identifier):
    pass


class PackageName(Identifier):
    pass


class RuntimeKind(Identifier):
    pass


class SourceSuffix(FixtureRootModel[str]):
    root: str = Field(pattern=r"^\.[a-z0-9]+$")

    @property
    def value(self) -> str:
        return self.root


class CapabilitySchemaVersion(FixtureRootModel[Literal[1]]):
    pass


class SourcePosition(FixtureRootModel[int]):
    root: int = Field(ge=0)


class SourceLine(FixtureRootModel[int]):
    root: int = Field(ge=1)


class ClaimState(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    UNSUPPORTED = "unsupported"


class RelationshipAspect(StrEnum):
    SEMANTICS = "semantics"
    INVENTORY = "inventory"


class TypeSlotRole(StrEnum):
    RETURN = "return"
    PARAMETER = "parameter"
    ATTRIBUTE = "attribute"


class FixtureRole(StrEnum):
    EXTENSIONS = "extensions"
    GAPS = "gaps"
    TYPES = "types"
    PARAMETERS = "parameters"


class ManifestChange(StrEnum):
    SOURCE_IDENTITY = "source_identity"
    IMPLEMENTATION_IDENTITY = "implementation_identity"


class RuntimePackageManager(StrEnum):
    GEM = "gem"
    NONE = "none"
