import os
import shutil
import subprocess
import sys
from pathlib import Path

from modwire.application import ModwireApplication
from tests.support.code_map_fixture.fixture_contract import PolyglotFixtureContract


class ExtractorBuildChecks:
    def __init__(self, repository: Path) -> None:
        self.repository = repository

    def run(self) -> int:
        PolyglotFixtureContract(self.repository).validate_runtime(ModwireApplication.create())
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
        environment = dict(os.environ)
        source_root = str(self.repository / "src")
        configured_paths = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            os.pathsep.join((source_root, configured_paths)) if configured_paths else source_root
        )
        module = ".".join(path.relative_to(self.repository / "src").with_suffix("").parts)
        subprocess.run(
            (sys.executable, "-m", module, str(path.parent), str(work)),
            check=True,
            env=environment,
        )


if __name__ == "__main__":
    raise SystemExit(ExtractorBuildChecks(Path(__file__).resolve().parents[1]).run())
