from typing import Self

from pydantic import ConfigDict, model_validator

from ...values.models.value_model import ValueModel
from .identity import FileId, ModuleId
from .source_file import SourceFile
from .source_manifest import SourceManifest


class SourceExtraction(ValueModel):
    model_config = ConfigDict(frozen=True)
    files: dict[FileId, SourceFile]
    modules: dict[ModuleId, FileId]
    manifest: SourceManifest
    files_found: int
    files_excluded: int
    directories_pruned: int

    @model_validator(mode="after")
    def validate_manifest_sources(self) -> Self:
        extracted = {str(file_id) for file_id in self.files}
        manifested = {source.source_id for source in self.manifest.sources}
        if extracted != manifested:
            raise ValueError("Source extraction files must exactly match the source manifest.")
        if self.files_found != len(self.manifest.sources):
            raise ValueError("Source extraction count must exactly match the source manifest.")
        if any(source_file.file_id != file_id for file_id, source_file in self.files.items()):
            raise ValueError("Source extraction file identities must match their map keys.")
        return self

    def files_dict(self) -> dict[FileId, SourceFile]:
        return dict(self.files)
