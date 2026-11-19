import re
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.dependencies.source_dependency_resolution import SourceDependencyResolution
from ....shared.code.models.sources.identity import FileId, ImportIdentity
from ....shared.code.models.sources.import_crossing_type import ImportCrossingType
from ....shared.code.models.sources.source_file import SourceFile
from ....shared.code.models.sources.source_import import SourceImport
from ..domain import ImportResolver
from .import_identity_index import ImportIdentityIndex


@injectable(as_type=ImportResolver)
@dataclass(frozen=True)
class SourceImportResolver(ImportResolver):
    def resolve(
        self, files: dict[FileId, SourceFile], identities: dict[FileId, tuple[ImportIdentity, ...]]
    ) -> dict[FileId, SourceFile]:
        modules = ImportIdentityIndex()
        symbols = ImportIdentityIndex()
        for file_id, source_file in files.items():
            for identity in identities[file_id]:
                modules.add("", self._normalize(identity), file_id)
            if not source_file.exports:
                continue
            module = self._normalize(source_file.import_identity)
            parent = module.rsplit("/", 1)[0] if "/" in module else ""
            for exported in source_file.exports:
                symbols.add(exported.name.casefold(), parent, file_id)
        resolved: dict[FileId, SourceFile] = {}
        for file_id, source_file in files.items():
            imports = [self._resolve_import(imported, modules, symbols) for imported in source_file.imports]
            if all(before is after for before, after in zip(source_file.imports, imports, strict=True)):
                resolved[file_id] = source_file
            else:
                resolved[file_id] = source_file.model_copy(update={"imports": imports})
        return resolved

    def _resolve_import(
        self, imported: SourceImport, modules: ImportIdentityIndex, symbols: ImportIdentityIndex
    ) -> SourceImport:
        candidates = self._candidates(imported, modules, symbols)
        target_file_id: FileId | None
        if len(candidates) == 1:
            resolution = SourceDependencyResolution.RESOLVED
            target_file_id = next(iter(candidates))
        else:
            resolution = (
                SourceDependencyResolution.UNRESOLVED
                if candidates or imported.is_relative
                else SourceDependencyResolution.EXTERNAL
            )
            target_file_id = None
        if imported.resolution is resolution and imported.target_file_id == target_file_id:
            return imported
        return imported.model_copy(
            update={
                "resolution": resolution,
                "target_file_id": target_file_id,
            }
        )

    def _candidates(
        self, imported: SourceImport, modules: ImportIdentityIndex, symbols: ImportIdentityIndex
    ) -> set[FileId]:
        specifier = self._normalize(imported.normalized_path)
        candidates = modules.exact("", specifier)
        if candidates:
            return candidates
        if imported.crossing_type is ImportCrossingType.SYMBOL and imported.imported_symbols:
            symbol_names = {symbol.name.casefold() for symbol in imported.imported_symbols}
            imported_parent = self._normalize(imported.join_key)
            for symbol_name in symbol_names:
                candidates.update(symbols.exact(symbol_name, imported_parent))
        if candidates:
            return candidates
        candidates = modules.suffix("", specifier)
        if candidates:
            return candidates
        if imported.crossing_type is ImportCrossingType.SYMBOL and imported.imported_symbols:
            symbol_names = {symbol.name.casefold() for symbol in imported.imported_symbols}
            imported_parent = self._normalize(imported.join_key)
            for symbol_name in symbol_names:
                candidates.update(symbols.suffix(symbol_name, imported_parent))
        return candidates

    def _normalize(self, value: str) -> str:
        return re.sub("[^a-z0-9/]", "", str(value).replace("\\", "/").strip("/").casefold())
