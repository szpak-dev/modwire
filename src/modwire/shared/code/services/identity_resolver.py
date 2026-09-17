from dataclasses import dataclass

from wireup import injectable

from ..domain import IdentityResolver
from ..models.identity import FileId, ModuleId


@injectable(as_type=IdentityResolver)
@dataclass(frozen=True)
class SourceIdentityResolver(IdentityResolver):
    def parts(self, value: str) -> tuple[str, ...]:
        return tuple(part for part in value.replace("\\", "/").split("/") if part and part != ".")

    def relative(self, root: str, path: str) -> tuple[str, ...]:
        root_parts = self.parts(root)
        path_parts = self.parts(path)
        if path_parts[: len(root_parts)] != root_parts:
            raise ValueError(f"Source path is outside its root: {path}")
        return path_parts[len(root_parts) :]

    def file_id(self, root: str, path: str) -> FileId:
        return FileId("/".join(self.relative(root, path)))

    def module_id(self, root: str, path: str) -> ModuleId:
        relative = list(self.relative(root, path))
        name, separator, _ = relative[-1].rpartition(".")
        if separator:
            relative[-1] = name
        return ModuleId("/".join(relative))
