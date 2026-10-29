from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import Field, model_validator

from ..model import FixtureModel
from .expectations.transition import ManifestTransitionExpectation


class LanguageCapabilityIndex(FixtureModel):
    schema_version: Literal[1]
    reference_projection: str = Field(min_length=1)
    parameter_kinds: tuple[str, ...] = Field(min_length=1)
    manifest_transitions: tuple[ManifestTransitionExpectation, ...] = Field(min_length=1)
    languages: dict[str, str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        if any(not language for language in self.languages):
            raise ValueError("language keys must not be empty")
        if len(set(self.parameter_kinds)) != len(self.parameter_kinds):
            raise ValueError("parameter-kind vocabulary contains duplicates")
        paths = tuple(PurePosixPath(path) for path in self.languages.values())
        if len(set(paths)) != len(paths):
            raise ValueError("language document paths contain duplicates")
        if any(path.is_absolute() or path.suffix != ".yaml" for path in paths):
            raise ValueError("language document paths must be relative YAML paths")
        if len({path.parent for path in paths}) != 1 or any(len(path.parts) != 2 for path in paths):
            raise ValueError("language documents must share one nested directory")
        if any(path.name != f"{language}.yaml" for language, path in zip(self.languages, paths, strict=True)):
            raise ValueError("language document filenames must match their language keys")
        return self
