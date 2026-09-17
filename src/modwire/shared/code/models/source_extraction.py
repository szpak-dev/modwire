from pydantic import ConfigDict

from ...values.models.value_model import ValueModel
from .identity import FileId, ModuleId
from .source_file import SourceFile


class SourceExtraction(ValueModel):
    model_config = ConfigDict(frozen=True)
    files: dict[FileId, SourceFile]
    modules: dict[ModuleId, FileId]
    files_found: int
    files_excluded: int

    def files_dict(self) -> dict[FileId, SourceFile]:
        return dict(self.files)
