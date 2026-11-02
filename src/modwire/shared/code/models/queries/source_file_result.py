from ....values.models.value_model import ValueModel
from ..sources.identity import FileId
from ..sources.source_file import SourceFile


class SourceFileResult(ValueModel):
    source_id: FileId
    file: SourceFile
