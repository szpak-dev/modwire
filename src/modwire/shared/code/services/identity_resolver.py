from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ..domain import IdentityResolver
from ..models.identity import FileId, ModuleId


@injectable(as_type=IdentityResolver)
@dataclass(frozen=True)
class PathIdentityResolver(IdentityResolver):
    def file_id(self, root: Path, path: Path) -> FileId:
        return FileId(path.relative_to(root).as_posix().strip("/"))

    def module_id(self, root: Path, path: Path) -> ModuleId:
        relative_path = path.relative_to(root)
        return ModuleId(relative_path.with_suffix("").as_posix().strip("/"))
