from abc import ABC, abstractmethod

from .models.cache_key import CacheKey
from .models.cache_options import CacheOptions


class CacheStorage(ABC):
    @abstractmethod
    def read(self, options: CacheOptions, key: CacheKey) -> bytes | None:
        raise NotImplementedError

    @abstractmethod
    def read_many(self, options: CacheOptions, keys: tuple[CacheKey, ...]) -> tuple[bytes | None, ...]:
        raise NotImplementedError

    @abstractmethod
    def write(self, options: CacheOptions, key: CacheKey, payload: bytes) -> bool:
        raise NotImplementedError

    @abstractmethod
    def write_many(self, options: CacheOptions, payloads: tuple[tuple[CacheKey, bytes], ...]) -> tuple[CacheKey, ...]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, options: CacheOptions, key: CacheKey) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_many(self, options: CacheOptions, keys: tuple[CacheKey, ...]) -> None:
        raise NotImplementedError

    @abstractmethod
    def enforce_capacity(self, options: CacheOptions) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear(self, options: CacheOptions) -> None:
        raise NotImplementedError
