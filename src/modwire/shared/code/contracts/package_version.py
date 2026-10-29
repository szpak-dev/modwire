from abc import ABC, abstractmethod


class PackageVersion(ABC):
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError
