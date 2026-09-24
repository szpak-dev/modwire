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

from pydantic import ValidationError
from wireup import injectable

from ..domain import CacheStorage
from ..models.cache_entry import CacheEntry
from ..models.cache_key import CacheKey
from ..models.cache_options import CacheOptions
from ..models.cache_storage_state import CacheStorageState


@injectable(as_type=CacheStorage)
@dataclass(frozen=True)
class FileCacheStorage(CacheStorage):
    _MARKER = ".modwire-cache-owner"
    _STATE = ".modwire-cache-state.json"
    _DIRTY = ".modwire-cache-dirty"

    def read(self, options: CacheOptions, key: CacheKey) -> bytes | None:
        return self.read_many(options, (key,))[0]

    def read_many(self, options: CacheOptions, keys: tuple[CacheKey, ...]) -> tuple[bytes | None, ...]:
        with self._locked(options):
            root = self._namespace_root(options)
            if not self._is_owned(root, options):
                return tuple(None for _ in keys)
            payloads: list[bytes | None] = []
            now = time.time_ns()
            for key in keys:
                path = self._entry_path(root, key)
                try:
                    payload = path.read_bytes()
                    status = path.stat()
                    os.utime(path, ns=(now, status.st_mtime_ns))
                    payloads.append(payload)
                except (FileNotFoundError, OSError):
                    payloads.append(None)
            return tuple(payloads)

    def write(self, options: CacheOptions, key: CacheKey, payload: bytes) -> bool:
        return bool(self.write_many(options, ((key, payload),)))

    def write_many(self, options: CacheOptions, payloads: tuple[tuple[CacheKey, bytes], ...]) -> tuple[CacheKey, ...]:
        if not payloads:
            return ()
        with self._locked(options):
            root = self._namespace_root(options)
            self._ensure_owned(root, options)
            state = self._state(root)
            total_bytes = state.total_bytes
            entry_count = state.entry_count
            dirty = self._dirty_path(root)
            dirty.write_text("dirty\n", encoding="utf-8")
            completed = False
            written: list[CacheKey] = []
            try:
                for key, payload in sorted(payloads, key=lambda item: (item[0].kind, item[0].digest)):
                    target = self._entry_path(root, key)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        existing = target.read_bytes()
                    except (FileNotFoundError, OSError):
                        existing = None
                    if existing == payload:
                        continue
                    try:
                        old_size = target.stat().st_size
                        existed = True
                    except (FileNotFoundError, OSError):
                        old_size = 0
                        existed = False
                    self._atomic_write(target, payload)
                    total_bytes += len(payload) - old_size
                    entry_count += int(not existed)
                    written.append(key)
                self._write_state(
                    root,
                    CacheStorageState(total_bytes=max(0, total_bytes), entry_count=max(0, entry_count)),
                )
                completed = True
            finally:
                if completed:
                    dirty.unlink(missing_ok=True)
            return tuple(written)

    def delete(self, options: CacheOptions, key: CacheKey) -> None:
        self.delete_many(options, (key,))

    def delete_many(self, options: CacheOptions, keys: tuple[CacheKey, ...]) -> None:
        if not keys:
            return
        with self._locked(options):
            root = self._namespace_root(options)
            if not self._is_owned(root, options):
                return
            state = self._state(root)
            total_bytes = state.total_bytes
            entry_count = state.entry_count
            dirty = self._dirty_path(root)
            dirty.write_text("dirty\n", encoding="utf-8")
            completed = False
            try:
                for key in sorted(set(keys), key=lambda item: (item.kind, item.digest)):
                    target = self._entry_path(root, key)
                    try:
                        size = target.stat().st_size
                        target.unlink()
                    except (FileNotFoundError, OSError):
                        continue
                    total_bytes -= size
                    entry_count -= 1
                self._write_state(
                    root,
                    CacheStorageState(total_bytes=max(0, total_bytes), entry_count=max(0, entry_count)),
                )
                completed = True
            finally:
                if completed:
                    dirty.unlink(missing_ok=True)

    def enforce_capacity(self, options: CacheOptions) -> bool:
        with self._locked(options):
            root = self._namespace_root(options)
            if not self._is_owned(root, options):
                return False
            state = self._state(root)
            if state.total_bytes <= options.max_bytes:
                return False
            entries = self._entries(root)
            total_bytes = sum(entry.size for entry in entries)
            retained = len(entries)
            dirty = self._dirty_path(root)
            dirty.write_text("dirty\n", encoding="utf-8")
            completed = False
            pruned = False
            try:
                for entry in sorted(entries, key=lambda item: (item.last_access_ns, item.key.kind, item.key.digest)):
                    if total_bytes <= options.max_bytes:
                        break
                    try:
                        self._entry_path(root, entry.key).unlink()
                    except (FileNotFoundError, OSError):
                        continue
                    total_bytes -= entry.size
                    retained -= 1
                    pruned = True
                self._write_state(
                    root,
                    CacheStorageState(total_bytes=max(0, total_bytes), entry_count=max(0, retained)),
                )
                completed = True
            finally:
                if completed:
                    dirty.unlink(missing_ok=True)
            return pruned

    def clear(self, options: CacheOptions) -> None:
        with self._locked(options):
            root = self._namespace_root(options)
            if not root.exists():
                return
            if not self._is_owned(root, options):
                raise RuntimeError(f"Refusing to clear a cache directory without Modwire ownership: {root}")
            shutil.rmtree(root)

    def _entries(self, root: Path) -> tuple[CacheEntry, ...]:
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

    def _state(self, root: Path) -> CacheStorageState:
        if self._dirty_path(root).exists():
            return self._recover_state(root)
        try:
            return CacheStorageState.model_validate_json(self._state_path(root).read_text(encoding="utf-8"))
        except (OSError, ValueError, ValidationError):
            return self._recover_state(root)

    def _recover_state(self, root: Path) -> CacheStorageState:
        entries = self._entries(root)
        state = CacheStorageState(total_bytes=sum(entry.size for entry in entries), entry_count=len(entries))
        self._write_state(root, state)
        self._dirty_path(root).unlink(missing_ok=True)
        return state

    def _write_state(self, root: Path, state: CacheStorageState) -> None:
        self._atomic_write(self._state_path(root), state.model_dump_json().encode())

    def _atomic_write(self, target: Path, payload: bytes) -> None:
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

    def _entry_path(self, root: Path, key: CacheKey) -> Path:
        return root / f"v{key.schema_version}" / key.kind / f"{key.digest}.cache"

    def _state_path(self, root: Path) -> Path:
        return root / self._STATE

    def _dirty_path(self, root: Path) -> Path:
        return root / self._DIRTY

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
