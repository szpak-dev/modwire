import shutil
import subprocess
import sys
from pathlib import Path


class ExtractorBuildChecks:
    def __init__(self, repository: Path) -> None:
        self.repository = repository

    def run(self) -> int:
        resources = self.repository / "src/modwire/extraction/extractors/resources"
        work_root = self.repository / ".dev/native"
        adapters = tuple(sorted(resources.glob("*/build.py")))
        if not adapters:
            raise RuntimeError(f"No extractor build adapters found beneath: {resources}")
        for path in adapters:
            self.check(path, work_root / path.parent.name)
        return 0

    def check(self, path: Path, work: Path) -> None:
        shutil.rmtree(work, ignore_errors=True)
        subprocess.run((sys.executable, str(path), str(path.parent), str(work)), check=True)


if __name__ == "__main__":
    raise SystemExit(ExtractorBuildChecks(Path(__file__).resolve().parents[1]).run())
