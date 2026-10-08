from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.identity import FileId, ModuleId
from ......shared.code.models.source_file import SourceFile


class PythonModuleIdentityPolicy(ABC):
    @abstractmethod
    def identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ModuleId, ...]]:
        raise NotImplementedError


@injectable(as_type=PythonModuleIdentityPolicy)
@dataclass(frozen=True)
class PackageModuleIdentityPolicy(PythonModuleIdentityPolicy):
    def identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ModuleId, ...]]:
        package_modules = {
            str(source_file.module_id).removesuffix("/__init__")
            for source_file in files.values()
            if str(source_file.module_id).endswith("/__init__")
        }
        identities: dict[FileId, tuple[ModuleId, ...]] = {}
        for file_id, source_file in files.items():
            module_id = source_file.module_id
            value = str(module_id)
            candidates = [module_id]
            if value.endswith("/__init__"):
                candidates.append(ModuleId(value.rsplit("/", 1)[0]))
            parts = value.split("/")
            package_start = len(parts) - 1
            for index in range(len(parts) - 2, -1, -1):
                if "/".join(parts[: index + 1]) not in package_modules:
                    break
                package_start = index
            if package_start < len(parts) - 1:
                import_parts = parts[package_start:]
                if import_parts[-1] == "__init__":
                    import_parts = import_parts[:-1]
                if import_parts:
                    candidates.append(ModuleId("/".join(import_parts)))
            identities[file_id] = tuple(dict.fromkeys(candidates))
        return identities
