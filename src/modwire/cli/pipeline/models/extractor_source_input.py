from pathlib import Path

from ....shared.code.models.identity import FileId
from ....shared.values.models.value_model import ValueModel


class ExtractorSourceInput(ValueModel):
    source_id: FileId
    path: Path
    root: Path
    content: str
