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
            raise ExtractorInvariantError(ExtractorInvariantViolation.INVALID_BUILD_ARGUMENTS, "php")
        try:
            self.check(Path(arguments[1]), Path(arguments[2]))
        except OSError as error:
            raise ExtractorInvariantError(ExtractorInvariantViolation.BUILD_RESOURCE_ACCESS_FAILED, "php") from error
        return 0

    def check(self, source: Path, work: Path) -> None:
        shutil.copytree(source, work, ignore=shutil.ignore_patterns("build.py", "__pycache__"))
        environment = dict(os.environ)
        environment["COMPOSER_CACHE_DIR"] = str(work.parent.parent / "cache/composer")
        self.run(
            ("composer", "install", "--no-interaction", "--no-progress", "--prefer-dist"),
            cwd=work,
            environment=environment,
        )
        self.run(("composer", "check"), cwd=work, environment=environment)
        self.run(("composer", "build"), cwd=work, environment=environment)
        if (work / "script.php").read_bytes() != (source / "script.php").read_bytes():
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.STALE_GENERATED_RESOURCE, str(source / "script.php")
            )

    def run(self, command: tuple[str, ...], *, cwd: Path, environment: dict[str, str]) -> None:
        try:
            subprocess.run(command, cwd=cwd, env=environment, check=True)
        except subprocess.CalledProcessError as error:
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.BUILD_COMMAND_FAILED, " ".join(command)
            ) from error


if __name__ == "__main__":
    raise SystemExit(BuildAdapter().execute(sys.argv))
