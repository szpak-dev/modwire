from abc import ABC, abstractmethod


class PathMatcher(ABC):
    @abstractmethod
    def match(self, path: str, pattern: str, *, scope: bool) -> tuple[str, ...] | None:
        raise NotImplementedError
