from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from .domain import IdentityResolver
from .models.code_map import CodeMap
from .models.identity import FileId, ModuleId
from .models.queryable_code_map import QueryableCodeMap


@injectable
@dataclass(frozen=True)
class CodeApplication:
    identities: IdentityResolver

    def file_id(self, root: Path, path: Path) -> FileId:
        return self.identities.file_id(root, path)

    def module_id(self, root: Path, path: Path) -> ModuleId:
        return self.identities.module_id(root, path)

    def queryable(self, code_map: CodeMap) -> QueryableCodeMap:
        return QueryableCodeMap(code_map=code_map)
