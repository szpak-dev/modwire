from typing import Self

from pydantic import Field, model_validator

from ....extraction.extractors.models.extraction_request import ExtractionRequest
from ....shared.code.models.source_manifest import SourceManifest
from ....shared.code.models.source_manifest_identity import SourceManifestIdentity
from ....shared.values.models.value_model import ValueModel
from .source_entry import SourceEntry


class SourceObservation(ValueModel):
    request: ExtractionRequest
    entries: tuple[SourceEntry, ...]
    files_found: int = Field(ge=0)
    files_excluded: int = Field(ge=0)
    directories_pruned: int = Field(ge=0)
    manifest: SourceManifest

    def identity(self) -> SourceManifestIdentity:
        return self.manifest.identity()

    @model_validator(mode="after")
    def validate_observation(self) -> Self:
        if self.files_found != len(self.entries):
            raise ValueError("Source observation files_found must equal its entry count.")
        artifacts = tuple(entry.artifact() for entry in self.entries)
        if artifacts != self.manifest.sources:
            raise ValueError("Source observation entries must match its canonical manifest.")
        return self
