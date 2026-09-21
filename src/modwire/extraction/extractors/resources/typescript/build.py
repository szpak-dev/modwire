from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class BuildAdapter:
    @staticmethod
    def check(source: Path, work: Path) -> None:
        shutil.copytree(source, work, ignore=shutil.ignore_patterns("build.py", "__pycache__"))
        environment = dict(os.environ)
        environment["npm_config_cache"] = str(work.parent.parent / "cache/npm")
        BuildAdapter.run(("npm", "ci"), cwd=work, environment=environment)
        BuildAdapter.run(("npm", "run", "check"), cwd=work, environment=environment)
        BuildAdapter.run(("npm", "run", "build"), cwd=work, environment=environment)
        if (work / "script.js").read_bytes() != (source / "script.js").read_bytes():
            raise RuntimeError(f"Generated extractor resource is stale: {source / 'script.js'}")

    @staticmethod
    def run(command: tuple[str, ...], *, cwd: Path, environment: dict[str, str]) -> None:
        subprocess.run(command, cwd=cwd, env=environment, check=True)
