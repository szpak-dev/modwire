import re
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import FileId
from ....shared.code.models.source_file import SourceFile
from ....shared.code.models.source_import import SourceImport
from ..domain import ImportResolver
from .suffix_index import SuffixIndex


@injectable(as_type=ImportResolver)
@dataclass(frozen=True)
class SourceImportResolver(ImportResolver):
    def resolve(self, files: dict[FileId, SourceFile]) -> dict[FileId, SourceFile]:
        modules = SuffixIndex()
        symbols = SuffixIndex()
        for file_id, source_file in files.items():
            module = self._normalize(source_file.module_id)
            modules.add("", module, file_id)
            parent = module.rsplit("/", 1)[0] if "/" in module else ""
            for exported in source_file.exports:
                symbols.add(exported.name.casefold(), parent, file_id)
        return {
            file_id: source_file.model_copy(
                update={
                    "imports": [self._resolve_import(imported, modules, symbols) for imported in source_file.imports]
                }
            )
            for file_id, source_file in files.items()
        }

    def _resolve_import(self, imported: SourceImport, modules: SuffixIndex, symbols: SuffixIndex) -> SourceImport:
        specifier = self._normalize(imported.normalized_path)
        candidates = modules.find("", specifier)
        if imported.crossing_type == "symbol" and imported.imported_symbols:
            symbol_names = {symbol.name.casefold() for symbol in imported.imported_symbols}
            imported_parent = self._normalize(imported.join_key)
            for symbol_name in symbol_names:
                candidates.update(symbols.find(symbol_name, imported_parent))
        if len(candidates) == 1:
            return imported.model_copy(update={"resolution": "resolved", "target_file_id": next(iter(candidates))})
        return imported.model_copy(
            update={
                "resolution": "unresolved" if candidates or imported.is_relative else "external",
                "target_file_id": None,
            }
        )

    def _normalize(self, value: str) -> str:
        parts = str(value).replace("\\", "/").strip("/").split("/")
        return "/".join(re.sub("[^a-z0-9]", "", part.casefold()) for part in parts)
