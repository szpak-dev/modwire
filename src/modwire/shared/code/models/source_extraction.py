from pydantic import ConfigDict

from modwire.shared.code.models.identity import FileId, ModuleId
from modwire.shared.code.models.source_file import SourceFile
from modwire.shared.values.models.value_model import ValueModel


class SourceExtraction(ValueModel):
    model_config = ConfigDict(frozen=True)
    files: dict[FileId, SourceFile]
    modules: dict[ModuleId, FileId]
    files_found: int
    files_excluded: int

    def files_dict(self) -> dict[FileId, SourceFile]:
        return dict(self.files)
