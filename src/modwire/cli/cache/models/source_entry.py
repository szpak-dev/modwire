from ....shared.code.models.identity import FileId
from ....shared.values.models.value_model import ValueModel


class SourceEntry(ValueModel):
    source_id: FileId
    relative_path: str
    content_digest: str
    path: str
