import os
import shutil
import subprocess
import sys
from pathlib import Path


class BuildAdapter:
    def execute(self, arguments: list[str]) -> int:
        if len(arguments) != 3:
            raise RuntimeError("Usage: build.py SOURCE WORK")
        self.check(Path(arguments[1]), Path(arguments[2]))
        return 0

    def check(self, source: Path, work: Path) -> None:
        shutil.copytree(source, work, ignore=shutil.ignore_patterns("build.py", "__pycache__"))
        environment = dict(os.environ)
        environment["npm_config_cache"] = str(work.parent.parent / "cache/npm")
        self.run(("npm", "ci", "--engine-strict"), cwd=work, environment=environment)
        self.run(("npm", "run", "check"), cwd=work, environment=environment)
        self.run(("npm", "run", "build"), cwd=work, environment=environment)
        if (work / "script.js").read_bytes() != (source / "script.js").read_bytes():
            raise RuntimeError(f"Generated extractor resource is stale: {source / 'script.js'}")

    def run(self, command: tuple[str, ...], *, cwd: Path, environment: dict[str, str]) -> None:
        subprocess.run(command, cwd=cwd, env=environment, check=True)


if __name__ == "__main__":
    raise SystemExit(BuildAdapter().execute(sys.argv))
