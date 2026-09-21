import hashlib
import importlib
import os
import shutil
import tempfile
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from wireup import injectable

from ..domain import CacheStorage
from ..models.cache_entry import CacheEntry
from ..models.cache_key import CacheKey
from ..models.cache_options import CacheOptions


@injectable(as_type=CacheStorage)
@dataclass(frozen=True)
class FileCacheStorage(CacheStorage):
    _MARKER = ".modwire-cache-owner"

    def read(self, options: CacheOptions, key: CacheKey) -> bytes | None:
        with self._locked(options):
            root = self._namespace_root(options)
            if not self._is_owned(root, options):
                return None
            path = self._entry_path(root, key)
            try:
                payload = path.read_bytes()
                status = path.stat()
                now = time.time_ns()
                os.utime(path, ns=(now, status.st_mtime_ns))
                return payload
            except (FileNotFoundError, OSError):
                return None

    def write(self, options: CacheOptions, key: CacheKey, payload: bytes) -> None:
        with self._locked(options):
            root = self._namespace_root(options)
            self._ensure_owned(root, options)
            target = self._entry_path(root, key)
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix=".modwire-", suffix=".tmp", dir=target.parent)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)

    def entries(self, options: CacheOptions) -> tuple[CacheEntry, ...]:
        with self._locked(options):
            root = self._namespace_root(options)
            if not self._is_owned(root, options):
                return ()
            entries: list[CacheEntry] = []
            for path in sorted(root.glob("v*/*/*.cache")):
                try:
                    version = int(path.parents[1].name.removeprefix("v"))
                    key = CacheKey.model_validate(
                        {"schema_version": version, "kind": path.parent.name, "digest": path.stem}
                    )
                    status = path.stat()
                    entries.append(CacheEntry(key=key, size=status.st_size, last_access_ns=status.st_atime_ns))
                except (OSError, ValueError):
                    continue
            return tuple(entries)

    def delete(self, options: CacheOptions, key: CacheKey) -> None:
        with self._locked(options):
            root = self._namespace_root(options)
            if self._is_owned(root, options):
                self._entry_path(root, key).unlink(missing_ok=True)

    def clear(self, options: CacheOptions) -> None:
        with self._locked(options):
            root = self._namespace_root(options)
            if not root.exists():
                return
            if not self._is_owned(root, options):
                raise RuntimeError(f"Refusing to clear a cache directory without Modwire ownership: {root}")
            shutil.rmtree(root)

    def _entry_path(self, root: Path, key: CacheKey) -> Path:
        return root / f"v{key.schema_version}" / key.kind / f"{key.digest}.cache"

    def _namespace_root(self, options: CacheOptions) -> Path:
        directory = Path(options.directory).expanduser().resolve()
        namespace_digest = hashlib.sha256(options.namespace.encode()).hexdigest()[:24]
        root = directory / f"namespace-{namespace_digest}"
        if root.parent != directory:
            raise RuntimeError(f"Invalid cache namespace root: {root}")
        return root

    def _ensure_owned(self, root: Path, options: CacheOptions) -> None:
        marker = root / self._MARKER
        if root.exists() and not marker.is_file() and any(root.iterdir()):
            raise RuntimeError(f"Refusing to use a cache directory without Modwire ownership: {root}")
        root.mkdir(parents=True, exist_ok=True)
        if marker.is_file():
            if marker.read_text(encoding="utf-8") != f"{options.namespace}\n":
                raise RuntimeError(f"Cache ownership marker does not match namespace: {root}")
            return
        marker.write_text(f"{options.namespace}\n", encoding="utf-8")

    def _is_owned(self, root: Path, options: CacheOptions) -> bool:
        marker = root / self._MARKER
        try:
            return marker.is_file() and marker.read_text(encoding="utf-8") == f"{options.namespace}\n"
        except OSError:
            return False

    @contextmanager
    def _locked(self, options: CacheOptions) -> Generator[None, None, None]:
        directory = Path(options.directory).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        namespace_digest = hashlib.sha256(options.namespace.encode()).hexdigest()[:24]
        lock_path = directory / f".namespace-{namespace_digest}.lock"
        with lock_path.open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            module = importlib.import_module("msvcrt" if os.name == "nt" else "fcntl")
            self._acquire(module, handle.fileno())
            try:
                yield
            finally:
                self._release(module, handle.fileno())

    def _acquire(self, module: ModuleType, descriptor: int) -> None:
        if os.name == "nt":
            module.locking(descriptor, module.LK_LOCK, 1)
        else:
            module.flock(descriptor, module.LOCK_EX)

    def _release(self, module: ModuleType, descriptor: int) -> None:
        if os.name == "nt":
            module.locking(descriptor, module.LK_UNLCK, 1)
        else:
            module.flock(descriptor, module.LOCK_UN)
