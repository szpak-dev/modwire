from ...values.models.value_model import ValueModel
from .identity import FileId
from .source_file import SourceFile


class SourceFileResult(ValueModel):
    source_id: FileId
    file: SourceFile
