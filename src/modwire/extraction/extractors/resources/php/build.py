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
        environment["COMPOSER_CACHE_DIR"] = str(work.parent.parent / "cache/composer")
        BuildAdapter.run(
            ("composer", "install", "--no-interaction", "--no-progress", "--prefer-dist"),
            cwd=work,
            environment=environment,
        )
        BuildAdapter.run(("composer", "check"), cwd=work, environment=environment)
        BuildAdapter.run(("composer", "build"), cwd=work, environment=environment)
        if (work / "script.php").read_bytes() != (source / "script.php").read_bytes():
            raise RuntimeError(f"Generated extractor resource is stale: {source / 'script.php'}")

    @staticmethod
    def run(command: tuple[str, ...], *, cwd: Path, environment: dict[str, str]) -> None:
        subprocess.run(command, cwd=cwd, env=environment, check=True)
