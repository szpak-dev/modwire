from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.identity import ImportSpecifier
from ...observations.import_candidate import PythonImportCandidate
from ...observations.source_context import PythonSourceContext


class PythonImportPathPolicy(ABC):
    @abstractmethod
    def normalize(self, candidate: PythonImportCandidate, context: PythonSourceContext) -> ImportSpecifier:
        raise NotImplementedError


@injectable(as_type=PythonImportPathPolicy)
@dataclass(frozen=True)
class RelativeImportPathPolicy(PythonImportPathPolicy):
    def normalize(self, candidate: PythonImportCandidate, context: PythonSourceContext) -> ImportSpecifier:
        if not candidate.is_relative:
            return ImportSpecifier(self.module_path(candidate.path))
        level = len(candidate.path) - len(candidate.path.lstrip("."))
        module = candidate.path[level:]
        package_parts = self.relative_parts(context.path, context.sources_root)[:-1]
        for _ in range(max(level - 1, 0)):
            if package_parts:
                package_parts.pop()
        package_path = "/".join(package_parts)
        module_path = self.module_path(module)
        return ImportSpecifier("/".join(part for part in (package_path, module_path) if part))

    def module_path(self, value: str) -> str:
        return value.replace(".", "/").strip("/")

    def relative_parts(self, path: str, sources_root: str) -> list[str]:
        path_parts = self.parts(path)
        root_parts = self.parts(sources_root)
        if path_parts[: len(root_parts)] == root_parts:
            return path_parts[len(root_parts) :]
        return path_parts[-1:]

    def parts(self, value: str) -> list[str]:
        return [part for part in value.replace("\\", "/").split("/") if part and part != "."]
