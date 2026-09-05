from ...values.models.value_model import ValueModel
from .identity import ImportSpecifier
from .types import ImportCrossingType, SourceExportKind


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
