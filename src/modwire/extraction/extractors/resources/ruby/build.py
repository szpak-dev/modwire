import shutil
import subprocess
import sys
from pathlib import Path

from modwire.extraction.extractors.models.extractor_invariant_error import ExtractorInvariantError
from modwire.extraction.extractors.models.extractor_invariant_violation import ExtractorInvariantViolation


class BuildAdapter:
    def execute(self, arguments: list[str]) -> int:
        if len(arguments) != 3:
            raise ExtractorInvariantError(ExtractorInvariantViolation.INVALID_BUILD_ARGUMENTS, "ruby")
        try:
            self.check(Path(arguments[1]), Path(arguments[2]))
        except OSError as error:
            raise ExtractorInvariantError(ExtractorInvariantViolation.BUILD_RESOURCE_ACCESS_FAILED, "ruby") from error
        return 0

    def check(self, source: Path, work: Path) -> None:
        shutil.copytree(source, work, ignore=shutil.ignore_patterns("build.py", "__pycache__"))
        self.run(
            (
                "ruby",
                "-rprism",
                "-e",
                (
                    'abort "Ruby 4.0.x and Prism 1.9.x are required." unless '
                    'RUBY_VERSION.start_with?("4.0.") && Prism::VERSION.start_with?("1.9.")'
                ),
            ),
            cwd=work,
        )
        self.run(("ruby", "-c", "script.rb"), cwd=work)

    def run(self, command: tuple[str, ...], *, cwd: Path) -> None:
        try:
            subprocess.run(command, cwd=cwd, check=True)
        except subprocess.CalledProcessError as error:
            raise ExtractorInvariantError(
                ExtractorInvariantViolation.BUILD_COMMAND_FAILED, " ".join(command)
            ) from error


if __name__ == "__main__":
    raise SystemExit(BuildAdapter().execute(sys.argv))
