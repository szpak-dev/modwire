from typing import Self

from pydantic import ConfigDict, model_validator

from ...values.models.value_model import ValueModel
from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation
from .identity import FileId, ImportIdentity
from .source_file import SourceFile
from .source_manifest import SourceManifest


class SourceExtraction(ValueModel):
    model_config = ConfigDict(frozen=True)
    files: dict[FileId, SourceFile]
    import_identities: dict[ImportIdentity, FileId]
    manifest: SourceManifest
    files_found: int
    files_excluded: int
    directories_pruned: int

    @model_validator(mode="after")
    def validate_manifest_sources(self) -> Self:
        extracted = {str(file_id) for file_id in self.files}
        manifested = {source.source_id for source in self.manifest.sources}
        if extracted != manifested:
            raise CodeValidationError(CodeViolation.SOURCE_SET_MISMATCH, "source extraction")
        if self.files_found != len(self.manifest.sources):
            raise CodeValidationError(CodeViolation.SOURCE_COUNT_MISMATCH, str(self.files_found))
        if any(source_file.file_id != file_id for file_id, source_file in self.files.items()):
            raise CodeValidationError(CodeViolation.SOURCE_FILE_IDENTITY_MISMATCH, "source extraction")
        expected_import_identities = {
            source_file.import_identity: file_id for file_id, source_file in self.files.items()
        }
        if self.import_identities != expected_import_identities:
            raise CodeValidationError(CodeViolation.IMPORT_IDENTITY_INDEX_MISMATCH, "source extraction")
        return self

    def files_dict(self) -> dict[FileId, SourceFile]:
        return dict(self.files)
