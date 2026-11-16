import hashlib
import inspect
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from modwire.application import ModwireApplication

from ..project import Project
from .provenance import ProfileProvenance
from .result import ProfileResult
from .snapshot import ProfileSnapshot
from .status import ProfileStatus


@dataclass(frozen=True)
class ProfileBenchmark:
    config: Path
    clone_root: Path
    output: Path
    limit_seconds: float = 20.0

    def run(self, projects: list[Project]) -> int:
        self.output.mkdir(parents=True, exist_ok=False)
        source_root = Path(inspect.getfile(ModwireApplication)).parent.parent
        source_paths = tuple(
            source_root / Path(path).relative_to("src")
            for path in sorted(
                subprocess.check_output(
                    ("git", "ls-files", "--cached", "--others", "--exclude-standard", "src"), text=True
                ).splitlines()
            )
        )
        provenance = ProfileProvenance(
            revision=subprocess.check_output(("git", "rev-parse", "HEAD"), text=True).strip(),
            source_digest=self.digest(source_paths),
            harness_digest=self.digest(tuple(sorted(Path(__file__).parent.parent.rglob("*.py")))),
            config_digest=self.digest((self.config,)),
            python_version=sys.version,
            limit_seconds=self.limit_seconds,
        )
        (self.output / "run.json").write_text(provenance.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (self.output / "result.schema.json").write_text(
            json.dumps(ProfileResult.model_json_schema(), indent=2) + "\n", encoding="utf-8"
        )
        (self.output / "calls.schema.json").write_text(
            json.dumps(ProfileSnapshot.model_json_schema(), indent=2) + "\n", encoding="utf-8"
        )
        results = tuple(self.measure(project) for project in projects)
        return int(any(result.status is not ProfileStatus.PASSED for result in results))

    def digest(self, paths: tuple[Path, ...]) -> str:
        digest = hashlib.sha256()
        for path in paths:
            content = path.read_bytes()
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        return digest.hexdigest()

    def measure(self, project: Project) -> ProfileResult:
        directory = self.output / project.language / project.project_id
        directory.mkdir(parents=True)
        command = (
            sys.executable,
            "-u",
            "-m",
            "tests.extraction.big_projects.profiling",
            str(directory / "calls.json"),
            "--config",
            str(self.config),
            "--clone-root",
            str(self.clone_root),
            "--only",
            project.label,
            "--repeat",
            "1",
        )
        started = time.perf_counter()
        with (directory / "stdout.log").open("w") as stdout, (directory / "stderr.log").open("w") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                exit_code = process.wait(timeout=self.limit_seconds)
                status = ProfileStatus.PASSED if exit_code == 0 else ProfileStatus.FAILED
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait()
                status = ProfileStatus.TIMEOUT
        result = ProfileResult(
            test_id=project.label,
            project=project,
            status=status,
            exit_code=exit_code,
            wall_seconds=time.perf_counter() - started,
            limit_seconds=self.limit_seconds,
            command=command,
        )
        (directory / "result.json").write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(f"{project.label}: {status.value} ({result.wall_seconds:.3f}s)", flush=True)
        return result
