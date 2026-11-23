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
from .resource_reason import ProfileResourceReason
from .result import ProfileResult
from .snapshot import ProfileSnapshot
from .status import ProfileStatus


@dataclass(frozen=True)
class ProfileBenchmark:
    config: Path
    clone_root: Path
    output: Path
    limit_seconds: float = 15.0
    rss_limit_bytes: int = 2 * 1024**3
    process_limit: int = 4
    max_workers: int = 2
    resource_sampling_seconds: float = 0.1
    sampler_timeout_seconds: float = 0.25

    def run(self, projects: list[Project]) -> int:
        self.output.mkdir(parents=True, exist_ok=False)
        source_root = Path(inspect.getfile(ModwireApplication)).parent.parent
        source_names = subprocess.check_output(
            ("git", "ls-files", "--cached", "--others", "--exclude-standard", "src"), text=True
        ).splitlines()
        source_paths = tuple(
            path
            for path in (source_root / Path(name).relative_to("src") for name in sorted(source_names))
            if path.is_file()
        )
        provenance = ProfileProvenance(
            revision=subprocess.check_output(("git", "rev-parse", "HEAD"), text=True).strip(),
            source_digest=self.digest(source_paths, source_root),
            harness_digest=self.digest(
                tuple(sorted(Path(__file__).parent.parent.rglob("*.py"))), Path(__file__).parent.parent
            ),
            config_digest=self.digest((self.config,), self.config.parent),
            python_version=sys.version,
            limit_seconds=self.limit_seconds,
            rss_limit_bytes=self.rss_limit_bytes,
            process_limit=self.process_limit,
            max_workers=self.max_workers,
            resource_sampling_seconds=self.resource_sampling_seconds,
            sampler_timeout_seconds=self.sampler_timeout_seconds,
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

    def digest(self, paths: tuple[Path, ...], root: Path) -> str:
        digest = hashlib.sha256()
        for path in paths:
            name = path.relative_to(root).as_posix().encode("utf-8")
            content = path.read_bytes()
            digest.update(len(name).to_bytes(8, "big"))
            digest.update(name)
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
            "--profile-max-workers",
            str(self.max_workers),
        )
        started = time.perf_counter()
        peak_rss_bytes = 0
        peak_processes = 0
        resource_samples = 0
        resource_reason = ProfileResourceReason.WITHIN_LIMITS
        with (directory / "stdout.log").open("w") as stdout, (directory / "stderr.log").open("w") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                while True:
                    try:
                        rss_bytes, processes = self.process_group_resources(process.pid)
                    except (
                        OSError,
                        subprocess.CalledProcessError,
                        subprocess.TimeoutExpired,
                        ValueError,
                    ) as error:
                        stderr.write(f"Resource monitor failed: {error}\n")
                        resource_reason = ProfileResourceReason.MONITOR_FAILED
                        status = ProfileStatus.FAILED
                        break
                    peak_rss_bytes = max(peak_rss_bytes, rss_bytes)
                    peak_processes = max(peak_processes, processes)
                    resource_samples += 1
                    if rss_bytes > self.rss_limit_bytes:
                        resource_reason = ProfileResourceReason.RSS_LIMIT
                        status = ProfileStatus.RESOURCE_LIMIT
                        break
                    if processes > self.process_limit:
                        resource_reason = ProfileResourceReason.PROCESS_LIMIT
                        status = ProfileStatus.RESOURCE_LIMIT
                        break
                    remaining_seconds = self.limit_seconds - (time.perf_counter() - started)
                    if remaining_seconds <= 0:
                        status = ProfileStatus.TIMEOUT
                        break
                    try:
                        completed_code = process.wait(timeout=min(self.resource_sampling_seconds, remaining_seconds))
                    except subprocess.TimeoutExpired:
                        continue
                    status = ProfileStatus.PASSED if completed_code == 0 else ProfileStatus.FAILED
                    break
            finally:
                exit_code = self.stop(process)
        result = ProfileResult(
            test_id=project.label,
            project=project,
            status=status,
            exit_code=exit_code,
            wall_seconds=time.perf_counter() - started,
            limit_seconds=self.limit_seconds,
            rss_limit_bytes=self.rss_limit_bytes,
            process_limit=self.process_limit,
            max_workers=self.max_workers,
            peak_rss_bytes=peak_rss_bytes,
            peak_processes=peak_processes,
            resource_samples=resource_samples,
            resource_reason=resource_reason,
            command=command,
        )
        (directory / "result.json").write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(f"{project.label}: {status.value} ({result.wall_seconds:.3f}s)", flush=True)
        return result

    def process_group_resources(self, group: int) -> tuple[int, int]:
        document = subprocess.check_output(
            ("ps", "-axo", "pgid=,rss="), text=True, timeout=self.sampler_timeout_seconds
        )
        rss_bytes = 0
        processes = 0
        for line in document.splitlines():
            process_group, rss_kib = line.split()
            if int(process_group) == group:
                rss_bytes += int(rss_kib) * 1024
                processes += 1
        return rss_bytes, processes

    def stop(self, process: subprocess.Popen[bytes]) -> int:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return process.wait()
        return process.wait()
