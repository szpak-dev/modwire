from dataclasses import dataclass

from .....shared.code.models.identity import FileId


@dataclass(frozen=True)
class PythonSourceContext:
    source_id: FileId
    path: str
    sources_root: str
    content: str
