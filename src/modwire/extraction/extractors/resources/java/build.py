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
        repository = work.parent.parent / "cache/maven"
        environment["MAVEN_USER_HOME"] = str(repository / "home")
        self.run(
            (
                "sh",
                "./mvnw",
                "--batch-mode",
                "--no-transfer-progress",
                f"-Dmaven.repo.local={repository}",
                "clean",
                "verify",
            ),
            cwd=work,
            environment=environment,
        )
        generated = work / "target/script.jar"
        committed = source / "script.jar"
        if generated.read_bytes() != committed.read_bytes():
            raise RuntimeError(f"Generated extractor resource is stale: {committed}")

    def run(self, command: tuple[str, ...], *, cwd: Path, environment: dict[str, str]) -> None:
        subprocess.run(command, cwd=cwd, env=environment, check=True)


if __name__ == "__main__":
    raise SystemExit(BuildAdapter().execute(sys.argv))
