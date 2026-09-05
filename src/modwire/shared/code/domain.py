from abc import ABC, abstractmethod
from pathlib import Path

from .models.identity import FileId, ModuleId


class IdentityResolver(ABC):
    @abstractmethod
    def file_id(self, root: Path, path: Path) -> FileId:
        raise NotImplementedError

    @abstractmethod
    def module_id(self, root: Path, path: Path) -> ModuleId:
        raise NotImplementedError


class PathMatcher(ABC):
    @abstractmethod
    def match(self, path: str, pattern: str, *, scope: bool) -> tuple[str, ...] | None:
        raise NotImplementedError
