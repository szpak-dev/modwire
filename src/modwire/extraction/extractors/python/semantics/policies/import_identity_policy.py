from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.identity import FileId, ImportIdentity
from ......shared.code.models.source_file import SourceFile


class PythonImportIdentityPolicy(ABC):
    @abstractmethod
    def identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ImportIdentity, ...]]:
        raise NotImplementedError


@injectable(as_type=PythonImportIdentityPolicy)
@dataclass(frozen=True)
class PackageImportIdentityPolicy(PythonImportIdentityPolicy):
    def identities(self, files: dict[FileId, SourceFile]) -> dict[FileId, tuple[ImportIdentity, ...]]:
        package_modules = {
            str(source_file.import_identity).removesuffix("/__init__")
            for source_file in files.values()
            if str(source_file.import_identity).endswith("/__init__")
        }
        identities: dict[FileId, tuple[ImportIdentity, ...]] = {}
        for file_id, source_file in files.items():
            import_identity = source_file.import_identity
            value = str(import_identity)
            candidates = [import_identity]
            if value.endswith("/__init__"):
                candidates.append(ImportIdentity(value.rsplit("/", 1)[0]))
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
                    candidates.append(ImportIdentity("/".join(import_parts)))
            identities[file_id] = tuple(dict.fromkeys(candidates))
        return identities
