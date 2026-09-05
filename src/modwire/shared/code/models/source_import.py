from pydantic import Field

from ...values.models.value_model import ValueModel
from .identity import FileId, ImportSpecifier
from .source_imported_symbol import SourceImportedSymbol
from .types import ImportCrossingType, SourceImportResolution


class SourceImport(ValueModel):
    path: ImportSpecifier
    is_relative: bool
    normalized_path: ImportSpecifier
    imported_name: str
    is_aliased: bool
    crossing_type: ImportCrossingType
    file_barrier_crossed: bool
    statement_id: int
    join_key: str
    uses_joined_import: bool
    resolution: SourceImportResolution = "unresolved"
    target_file_id: FileId | None = None
    imported_symbols: list[SourceImportedSymbol] = Field(default_factory=list[SourceImportedSymbol])
