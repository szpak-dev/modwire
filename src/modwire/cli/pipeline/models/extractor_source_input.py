from pathlib import Path

from ....shared.values.models.value_model import ValueModel


class ExtractorSourceInput(ValueModel):
    source_id: str
    path: Path
    root: Path
    content: str
