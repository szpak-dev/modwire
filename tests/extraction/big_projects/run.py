from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from modwire.application import ModwireApplication, ScanPolicy

from .project import Project


class BigProjectBenchmark:
    repository_root = Path(__file__).resolve().parents[3]
    default_config = Path(__file__).with_name("projects.json")

    def __init__(
        self, config: dict[str, Any], clone_root: Path, refresh: bool, operation: str, repetitions: int
    ) -> None:
        self.config = config
        self.clone_root = clone_root
        self.refresh = refresh
        self.operation = operation
        self.repetitions = repetitions
        self.application = ModwireApplication.create()

    @classmethod
    def main(cls) -> int:
        parser = argparse.ArgumentParser(description="Measure Modwire extraction on large public projects.")
        parser.add_argument("--config", type=Path, default=cls.default_config)
        parser.add_argument("--clone-root", type=Path)
        parser.add_argument("--refresh", action="store_true")
        parser.add_argument("--operation", choices=("discover", "extract"), default="discover")
        parser.add_argument("--repeat", type=int, default=3)
        parser.add_argument("--only", metavar="LANGUAGE/PROJECT", action="append", default=[])
        arguments = parser.parse_args()
        if arguments.repeat < 1:
            parser.error("--repeat must be at least 1")
        config = cls.load_config(arguments.config)
        configured_root = cls.repository_root / config["github"]["clone_root"]
        benchmark = cls(
            config,
            arguments.clone_root or configured_root,
            arguments.refresh,
            arguments.operation,
            arguments.repeat,
        )
        return benchmark.run(set(arguments.only))

    @staticmethod
    def load_config(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
        if not isinstance(config, dict):
            raise ValueError("Big-project config must be a JSON object.")
        return config

    def run(self, selected: set[str]) -> int:
        projects = [project for project in self.projects() if not selected or project.label in selected]
        missing = sorted(selected - {project.label for project in projects})
        if missing:
            print(f"Unknown project label(s): {', '.join(missing)}", file=sys.stderr)
            return 2
        self.clone_root.mkdir(parents=True, exist_ok=True)
        print(f"Big project root: {self.clone_root}")
        print(f"Projects: {len(projects)}")
        failures = sum(not self.measure(project) for project in projects)
        return 1 if failures else 0

    def projects(self) -> list[Project]:
        configured = self.config.get("projects")
        if not isinstance(configured, dict):
            raise ValueError("Big-project config must contain a projects object.")
        projects: list[Project] = []
        for language, entries in configured.items():
            if not isinstance(language, str) or not isinstance(entries, list):
                raise ValueError("Project mapping must be language names to arrays.")
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError(f"Invalid project entry for {language}.")
                projects.append(
                    Project(
                        language=language,
                        project_id=self.required_string(entry, "id"),
                        owner=self.required_string(entry, "owner"),
                        repository=self.required_string(entry, "repo"),
                        revision=self.required_string(entry, "revision"),
                    )
                )
        return projects

    def measure(self, project: Project) -> bool:
        project_root = self.clone_root / project.language / project.project_id
        started = time.perf_counter()
        print(f"\n{project.label} ({project.full_name})")
        try:
            sync_seconds = self.synchronize(project, project_root)
            if self.operation == "discover":
                self.measure_discovery(project_root, sync_seconds, started)
            else:
                self.measure_extraction(project, project_root, sync_seconds, started)
            return True
        except Exception as error:
            print(f"  failed after {time.perf_counter() - started:.2f}s: {error}", file=sys.stderr)
            return False

    def measure_discovery(self, project_root: Path, sync_seconds: float, started: float) -> None:
        durations: list[float] = []
        languages: tuple[str, ...] = ()
        for _ in range(self.repetitions):
            scan_started = time.perf_counter()
            languages = self.application.discover(project_root, self.scan_policy())
            durations.append(time.perf_counter() - scan_started)
        formatted = ",".join(f"{duration:.3f}" for duration in durations)
        print(
            "  "
            f"sync={sync_seconds:.2f}s "
            f"scan_median={statistics.median(durations):.3f}s "
            f"scan_runs=[{formatted}] "
            f"languages={','.join(languages)} "
            f"total={time.perf_counter() - started:.2f}s"
        )

    def measure_extraction(self, project: Project, project_root: Path, sync_seconds: float, started: float) -> None:
        extract_started = time.perf_counter()
        code_map = self.application.generate_map(project.language, project_root, self.scan_policy())
        extract_seconds = time.perf_counter() - extract_started
        extraction = code_map.extraction
        print(
            "  "
            f"sync={sync_seconds:.2f}s "
            f"extract={extract_seconds:.2f}s "
            f"total={time.perf_counter() - started:.2f}s "
            f"files={extraction.files_found} "
            f"excluded_files={extraction.files_excluded} "
            f"pruned_directories={extraction.directories_pruned}"
        )

    def scan_policy(self) -> ScanPolicy:
        configured = self.config.get("scan")
        if not isinstance(configured, dict):
            raise ValueError("Big-project config must contain a scan object.")
        patterns = configured.get("excluded_patterns")
        if not isinstance(patterns, list) or not all(isinstance(pattern, str) for pattern in patterns):
            raise ValueError("scan.excluded_patterns must be an array of strings.")
        return ScanPolicy(excluded_patterns=tuple(patterns))

    def synchronize(self, project: Project, project_root: Path) -> float:
        started = time.perf_counter()
        if not project_root.exists():
            project_root.parent.mkdir(parents=True, exist_ok=True)
            self.clone(project, project_root)
        elif not (project_root / ".git").is_dir():
            raise RuntimeError(f"Existing path is not a git clone: {project_root}")
        elif self.refresh:
            self.pin_revision(project, project_root)
        actual_revision = self.read(["git", "rev-parse", "HEAD"], project_root)
        if actual_revision != project.revision:
            raise RuntimeError(
                f"Expected {project.label} revision {project.revision}, found {actual_revision}; use --refresh"
            )
        return time.perf_counter() - started

    def clone(self, project: Project, project_root: Path) -> None:
        clone_config = self.config["github"]["clone"]
        command = ["git", "clone"]
        if clone_config.get("depth"):
            command.extend(["--depth", str(clone_config["depth"])])
        if clone_config.get("single_branch"):
            command.append("--single-branch")
        if clone_config.get("tags") is False:
            command.append("--no-tags")
        command.extend([self.clone_url(project), str(project_root)])
        self.execute(command, self.repository_root)
        if self.read(["git", "rev-parse", "HEAD"], project_root) != project.revision:
            self.pin_revision(project, project_root)

    def pin_revision(self, project: Project, project_root: Path) -> None:
        command = ["git", "fetch", "--prune"]
        clone_config = self.config["github"]["clone"]
        if clone_config.get("depth"):
            command.append(f"--depth={clone_config['depth']}")
        if clone_config.get("tags") is False:
            command.append("--no-tags")
        command.extend(["origin", project.revision])
        self.execute(command, project_root)
        self.execute(["git", "checkout", "--detach", project.revision], project_root)

    def clone_url(self, project: Project) -> str:
        github = self.config["github"]
        return f"{github['scheme']}://{github['host']}/{project.full_name}.git"

    @staticmethod
    def required_string(entry: dict[str, Any], key: str) -> str:
        value = entry.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Project entry requires a non-empty {key!r} string.")
        return value

    @staticmethod
    def execute(command: list[str], working_directory: Path) -> None:
        result = subprocess.run(command, cwd=working_directory, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"{' '.join(command)} failed: {message}")

    @staticmethod
    def read(command: list[str], working_directory: Path) -> str:
        result = subprocess.run(command, cwd=working_directory, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"{' '.join(command)} failed: {message}")
        return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(BigProjectBenchmark.main())
