from dataclasses import dataclass

from .....shared.code.models.identity import ImportSpecifier
from .....shared.code.models.source_export_kind import SourceExportKind


@dataclass(frozen=True)
class PythonExportCandidate:
    name: str
    local_name: str
    kind: SourceExportKind
    path: ImportSpecifier
    is_relative: bool
    normalized_path: ImportSpecifier
    is_reexport: bool
    is_aliased: bool
    statement_id: int
    explicit: bool
