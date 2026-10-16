from dataclasses import dataclass

from wireup import injectable

from .domain import IdentityResolver
from .models.code_map import CodeMap
from .models.identity import FileId, ImportIdentity
from .models.queryable_code_map import QueryableCodeMap


@injectable
@dataclass(frozen=True)
class CodeApplication:
    identities: IdentityResolver

    def file_id(self, root: str, path: str) -> FileId:
        return self.identities.file_id(root, path)

    def import_identity(self, root: str, path: str) -> ImportIdentity:
        return self.identities.import_identity(root, path)

    def queryable(self, code_map: CodeMap) -> QueryableCodeMap:
        return QueryableCodeMap(code_map=code_map)
