from dataclasses import dataclass

from .....shared.code.models.declarations.source_unresolved_target import SourceUnresolvedTarget
from .....shared.code.models.sources.identity import ImportSpecifier
from .....shared.code.models.sources.source_export_kind import SourceExportKind
from .....shared.code.models.sources.source_resolved_export_binding import SourceResolvedExportBinding


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
    binding: SourceResolvedExportBinding | SourceUnresolvedTarget
