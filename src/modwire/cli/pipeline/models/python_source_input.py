from pathlib import Path

from modwire.shared.values.models.value_model import ValueModel


class PythonSourceInput(ValueModel):
    source_id: str
    path: Path
    root: Path
    content: str
