from __future__ import annotations

import importlib.util
import shutil
from collections.abc import Callable
from pathlib import Path
from types import ModuleType


def load_adapter(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"modwire_extractor_build_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load extractor build adapter: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    resources = repository / "src/modwire/extraction/extractors/resources"
    work_root = repository / ".dev/native"
    adapters = tuple(sorted(resources.glob("*/build.py")))
    if not adapters:
        raise RuntimeError(f"No extractor build adapters found beneath: {resources}")
    for path in adapters:
        work = work_root / path.parent.name
        shutil.rmtree(work, ignore_errors=True)
        adapter = getattr(load_adapter(path), "BuildAdapter", None)
        check = getattr(adapter, "check", None)
        if not callable(check):
            raise RuntimeError(f"Extractor build adapter has no BuildAdapter.check method: {path}")
        typed_check: Callable[[Path, Path], None] = check
        typed_check(path.parent, work)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
