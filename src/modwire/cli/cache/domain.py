from abc import ABC, abstractmethod

from .models.cache_entry import CacheEntry
from .models.cache_key import CacheKey
from .models.cache_options import CacheOptions


class CacheStorage(ABC):
    @abstractmethod
    def read(self, options: CacheOptions, key: CacheKey) -> bytes | None:
        raise NotImplementedError

    @abstractmethod
    def write(self, options: CacheOptions, key: CacheKey, payload: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def entries(self, options: CacheOptions) -> tuple[CacheEntry, ...]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, options: CacheOptions, key: CacheKey) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self, options: CacheOptions) -> None:
        raise NotImplementedError
