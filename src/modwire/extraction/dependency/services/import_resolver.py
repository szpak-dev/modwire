import re
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.identity import FileId
from ....shared.code.models.source_file import SourceFile
from ....shared.code.models.source_import import SourceImport
from ..domain import ImportResolver


@injectable(as_type=ImportResolver)
@dataclass(frozen=True)
class SourceImportResolver(ImportResolver):
    def resolve(self, files: dict[FileId, SourceFile]) -> dict[FileId, SourceFile]:
        modules: list[tuple[str, FileId]] = []
        symbols: list[tuple[str, str, FileId]] = []
        for file_id, source_file in files.items():
            module = self._normalize(source_file.module_id)
            modules.append((module, file_id))
            parent = module.rsplit("/", 1)[0] if "/" in module else ""
            for exported in source_file.exports:
                symbols.append((parent, exported.name.casefold(), file_id))
        return {
            file_id: source_file.model_copy(
                update={
                    "imports": [self._resolve_import(imported, modules, symbols) for imported in source_file.imports]
                }
            )
            for file_id, source_file in files.items()
        }

    def _resolve_import(
        self, imported: SourceImport, modules: list[tuple[str, FileId]], symbols: list[tuple[str, str, FileId]]
    ) -> SourceImport:
        specifier = self._normalize(imported.normalized_path)
        candidates = {file_id for module, file_id in modules if self._same_suffix(module, specifier)}
        if imported.crossing_type == "symbol" and imported.imported_symbols:
            symbol_names = {symbol.name.casefold() for symbol in imported.imported_symbols}
            imported_parent = self._normalize(imported.join_key)
            candidates.update(
                (
                    file_id
                    for module_parent, symbol_name, file_id in symbols
                    if symbol_name in symbol_names and self._same_suffix(module_parent, imported_parent)
                )
            )
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

    def _same_suffix(self, left: str, right: str) -> bool:
        if not left or not right:
            return left == right
        left_parts = left.split("/")
        right_parts = right.split("/")
        shared = 0
        for left_part, right_part in zip(reversed(left_parts), reversed(right_parts)):
            if left_part != right_part:
                break
            shared += 1
        return shared == min(len(left_parts), len(right_parts)) or shared >= 2
