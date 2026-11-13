from pydantic import Field

from ....values.models.value_model import ValueModel
from ..declarations.source_unresolved_target import SourceUnresolvedTarget
from .identity import ImportSpecifier
from .import_crossing_type import ImportCrossingType
from .source_export_kind import SourceExportKind
from .source_resolved_export_binding import SourceResolvedExportBinding


class SourceExport(ValueModel):
    name: str
    local_name: str
    kind: SourceExportKind
    crossing_type: ImportCrossingType
    path: ImportSpecifier
    is_relative: bool
    normalized_path: ImportSpecifier
    is_reexport: bool
    is_default: bool
    is_aliased: bool
    statement_id: int
    binding: SourceResolvedExportBinding | SourceUnresolvedTarget = Field(discriminator="kind")
