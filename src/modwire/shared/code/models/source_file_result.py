from modwire.shared.code.models.identity import FileId
from modwire.shared.code.models.source_file import SourceFile
from modwire.shared.values.models.value_model import ValueModel


class SourceFileResult(ValueModel):
    source_id: FileId
    file: SourceFile
