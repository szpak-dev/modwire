from abc import ABC, abstractmethod

from .models.identity import FileId, ModuleId


class IdentityResolver(ABC):
    @abstractmethod
    def file_id(self, root: str, path: str) -> FileId:
        raise NotImplementedError

    @abstractmethod
    def module_id(self, root: str, path: str) -> ModuleId:
        raise NotImplementedError


class PathMatcher(ABC):
    @abstractmethod
    def match(self, path: str, pattern: str, *, scope: bool) -> tuple[str, ...] | None:
        raise NotImplementedError
