from abc import ABC, abstractmethod

from ..models.sources.identity import FileId, ImportIdentity


class IdentityResolver(ABC):
    @abstractmethod
    def file_id(self, root: str, path: str) -> FileId:
        raise NotImplementedError

    @abstractmethod
    def import_identity(self, root: str, path: str) -> ImportIdentity:
        raise NotImplementedError
