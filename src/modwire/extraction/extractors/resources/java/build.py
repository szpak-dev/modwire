import os
import shutil
import subprocess
import sys
from pathlib import Path

from modwire.extraction.extractors.models.extractor_invariant_error import ExtractorInvariantError
from modwire.extraction.extractors.models.extractor_invariant_violation import ExtractorInvariantViolation


class BuildAdapter:
    def execute(self, arguments: list[str]) -> int:
        if len(arguments) != 3:
            raise ExtractorInvariantError(ExtractorInvariantViolation.INVALID_BUILD_ARGUMENTS, "java")
        try:
            self.check(Path(arguments[1]), Path(arguments[2]))
        except OSError as error:
            raise ExtractorInvariantError(ExtractorInvariantViolation.BUILD_RESOURCE_ACCESS_FAILED, "java") from error
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
            raise ExtractorInvariantError(ExtractorInvariantViolation.STALE_GENERATED_RESOURCE, str(committed))

    def run(self, command: tuple[str, ...], *, cwd: Path, environment: dict[str, str]) -> None:
        try:
            subprocess.run(command, cwd=cwd, env=environment, check=True)
        except subprocess.CalledProcessError as error:
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.BUILD_COMMAND_FAILED, " ".join(command)
            ) from error


if __name__ == "__main__":
    raise SystemExit(BuildAdapter().execute(sys.argv))
