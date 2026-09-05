from modwire.shared.code.models.identity import ImportSpecifier
from modwire.shared.code.models.types import ImportCrossingType, SourceExportKind
from modwire.shared.values.models.value_model import ValueModel


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
