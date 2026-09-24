from __future__ import annotations

import argparse
import json
import os
import signal
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import Any, cast

from modwire.application import CacheOptions, CodeMap, ModwireApplication, QueryableCodeMap, ScanPolicy

from .benchmark_process_timeout import BenchmarkProcessTimeout


class ReportBenchmark:
    def __init__(
        self,
        root: Path,
        language: str,
        cache_directory: Path,
        namespace: str,
        repetitions: int,
        configuration_seed: int,
        max_process_seconds: float,
        code_map_cache_file: Path | None,
        analysis_only: bool,
    ) -> None:
        self.root = root.resolve()
        self.language = language
        self.cache_directory = cache_directory.resolve()
        self.namespace = namespace
        self.repetitions = repetitions
        self.configuration_seed = configuration_seed
        self.max_process_seconds = max_process_seconds
        self.code_map_cache_file = code_map_cache_file.resolve() if code_map_cache_file is not None else None
        self.analysis_only = analysis_only
        self.current_scenario = "setup"
        self.current_phase = "validation"

    @classmethod
    def main(cls) -> int:
        parser = argparse.ArgumentParser(description="Measure cached-map and architecture-report phases.")
        parser.add_argument("--root", type=Path, required=True)
        parser.add_argument("--language", required=True)
        parser.add_argument("--cache-directory", type=Path, required=True)
        parser.add_argument("--cache-namespace", required=True)
        parser.add_argument("--repeat", type=int, default=1)
        parser.add_argument("--configuration-seed", type=int, default=35)
        parser.add_argument("--max-process-seconds", type=float, default=20.0)
        parser.add_argument(
            "--code-map-cache-file",
            type=Path,
            help="Load a persisted CodeMap cache envelope when its original runtime cache key is stale.",
        )
        parser.add_argument(
            "--analysis-only",
            action="store_true",
            help="Measure one uncached report calculation without report-cache probe, storage, or invalidation.",
        )
        parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
        arguments = parser.parse_args()
        if arguments.repeat < 1:
            parser.error("--repeat must be at least one")
        if arguments.max_process_seconds <= 0:
            parser.error("--max-process-seconds must be greater than zero")
        if not hasattr(signal, "setitimer"):
            parser.error("hard benchmark timeouts require signal.setitimer")
        if not arguments.worker:
            return cls._run_supervised(arguments.max_process_seconds)
        benchmark = cls(
            arguments.root,
            arguments.language,
            arguments.cache_directory,
            arguments.cache_namespace,
            arguments.repeat,
            arguments.configuration_seed,
            arguments.max_process_seconds,
            arguments.code_map_cache_file,
            arguments.analysis_only,
        )
        try:
            print(json.dumps(benchmark.measure(), indent=2, sort_keys=True), flush=True)
            return 0
        except BenchmarkProcessTimeout as error:
            print(
                json.dumps(
                    {
                        "event": "incomplete",
                        "scenario": error.scenario,
                        "phase": error.phase,
                        "limit_seconds": error.limit_seconds,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return 0

    @classmethod
    def _run_supervised(cls, max_process_seconds: float) -> int:
        cleanup_reserve = min(1.0, max_process_seconds * 0.1)
        supervisor_seconds = max_process_seconds - cleanup_reserve
        if Path(sys.argv[0]).resolve() == Path(__file__).resolve():
            entrypoint = [sys.executable, "-m", "tests.architecture.report_benchmark.run"]
        else:
            entrypoint = [sys.executable, sys.argv[0]]
        command = [*entrypoint, *sys.argv[1:], "--worker"]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=supervisor_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout, end="")
            if stderr:
                print(stderr, end="", file=sys.stderr)
            scenario, phase = cls._active_phase(stdout)
            print(
                json.dumps(
                    {
                        "event": "incomplete",
                        "scenario": scenario,
                        "phase": phase,
                        "limit_seconds": max_process_seconds,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            return 0
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, end="", file=sys.stderr)
        return process.returncode

    @staticmethod
    def _active_phase(stdout: str) -> tuple[str, str]:
        active = ("process", "unknown")
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "phase_started":
                active = (str(event["scenario"]), str(event["phase"]))
        return active

    def measure(self) -> dict[str, Any]:
        def timeout_handler(_signal_number: int, _frame: FrameType | None) -> None:
            raise BenchmarkProcessTimeout(self.current_scenario, self.current_phase, self.max_process_seconds)

        cleanup_reserve = min(1.0, self.max_process_seconds * 0.1)
        previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, self.max_process_seconds - cleanup_reserve)
        try:
            return self._measure()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)

    def _measure(self) -> dict[str, Any]:
        if not self.root.is_dir():
            raise RuntimeError(f"Benchmark root is not a directory: {self.root}")
        if self.code_map_cache_file is not None and not self.code_map_cache_file.is_file():
            raise RuntimeError(f"CodeMap cache file does not exist: {self.code_map_cache_file}")
        application = ModwireApplication.create()
        policy = ScanPolicy()
        request = application.extraction.request(self.language, str(self.root))
        options = CacheOptions(
            directory=str(self.cache_directory),
            namespace=self.namespace,
            max_bytes=2 * 1024 * 1024 * 1024,
        )
        base_limit = 1_000_000_000 + (self.configuration_seed * 2)
        permissive_shape = {
            "max_variables_per_file": -1,
            "allow_optional_function_args": True,
            "allow_optional_method_args": True,
            "allow_optional_class_properties": True,
            "allow_import_aliases": True,
            "require_joined_imports": False,
        }
        config = application.configure(
            {
                "shape": {
                    "realms": [
                        {
                            "name": "benchmark-source",
                            "match": "**",
                            "shape": {**permissive_shape, "max_functions_per_file": base_limit},
                        }
                    ]
                }
            }
        )
        invalidated_config = application.configure(
            {
                "shape": {
                    "realms": [
                        {
                            "name": "benchmark-source",
                            "match": "**",
                            "shape": {**permissive_shape, "max_functions_per_file": base_limit + 1},
                        }
                    ]
                }
            }
        )
        measurements: list[dict[str, float]] = []
        cache_observations: list[dict[str, bool]] = []
        files_checked = 0
        for repetition in range(1, self.repetitions + 1):
            measurement: dict[str, float] = {}
            cache_file = self.code_map_cache_file
            if cache_file is None:
                plan, measurement["inventory"] = self._phase(
                    repetition, "map", "inventory", lambda: application.cli.prepare_cache(request, policy)
                )
                cached_map, measurement["code_map_loading"] = self._phase(
                    repetition, "map", "code_map_loading", lambda: application.cli.cached_code_map(plan, options)
                )
                code_map = cached_map.value
                code_map_hit = code_map is not None
                if code_map is None:
                    sources, measurement["extraction_loading"] = self._phase(
                        repetition,
                        "map",
                        "extraction_loading",
                        lambda: application.cli.cached_sources(request, plan, options),
                    )
                    _, measurement["manifest_maintenance"] = self._phase(
                        repetition,
                        "map",
                        "manifest_maintenance",
                        lambda: application.cli.maintain_manifest(plan, options),
                    )
                    generated_map, measurement["code_map_construction"] = self._phase(
                        repetition,
                        "map",
                        "code_map_construction",
                        lambda: application.extraction.generate_map(self.language, sources.value),
                    )
                    _, measurement["code_map_storage"] = self._phase(
                        repetition,
                        "map",
                        "code_map_storage",
                        lambda: application.cli.store_code_map(plan, generated_map, options),
                    )
                    code_map = generated_map
                else:
                    for phase in (
                        "extraction_loading",
                        "manifest_maintenance",
                        "code_map_construction",
                        "code_map_storage",
                    ):
                        measurement[phase] = self._skipped_phase(repetition, "map", phase)
            else:
                measurement["inventory"] = self._skipped_phase(repetition, "map", "inventory")
                code_map, measurement["code_map_loading"] = self._phase(
                    repetition,
                    "map",
                    "code_map_loading",
                    lambda: self._load_code_map_cache(cast(Path, cache_file)),
                )
                code_map_hit = True
                for phase in (
                    "extraction_loading",
                    "manifest_maintenance",
                    "code_map_construction",
                    "code_map_storage",
                ):
                    measurement[phase] = self._skipped_phase(repetition, "map", phase)
            loaded_code_map = code_map
            if loaded_code_map.language != self.language:
                raise RuntimeError(
                    f"CodeMap language {loaded_code_map.language!r} does not match "
                    f"benchmark language {self.language!r}."
                )
            queryable = QueryableCodeMap(code_map=loaded_code_map)
            files_checked = len(loaded_code_map.extraction.files)
            if self.analysis_only:
                _, measurement["reporting"] = self._phase(
                    repetition,
                    "analysis",
                    "reporting",
                    lambda: application.analyze(queryable, config),
                )
                measurements.append(measurement)
                cache_observations.append({"code_map_hit": code_map_hit})
                continue
            cold_probe, measurement["cold_report_probe"] = self._phase(
                repetition,
                "cold",
                "report_probe",
                lambda: application.cli.cached_reports(loaded_code_map, config, options),
            )
            cold_reports, measurement["cold_reporting"] = self._phase(
                repetition,
                "cold",
                "reporting",
                lambda: application.analyze(queryable, config),
            )
            _, measurement["cold_report_storage"] = self._phase(
                repetition,
                "cold",
                "report_storage",
                lambda: application.cli.store_reports(loaded_code_map, config, cold_reports, options),
            )
            warm_reports, measurement["warm_report_loading"] = self._phase(
                repetition,
                "warm",
                "report_loading",
                lambda: application.cli.cached_reports(loaded_code_map, config, options),
            )
            if warm_reports.value is None:
                raise RuntimeError("Warm report cache entry was not reusable.")
            invalidated_probe, measurement["invalidated_report_probe"] = self._phase(
                repetition,
                "invalidated",
                "report_probe",
                lambda: application.cli.cached_reports(loaded_code_map, invalidated_config, options),
            )
            _, measurement["invalidated_reporting"] = self._phase(
                repetition,
                "invalidated",
                "reporting",
                lambda: application.analyze(queryable, invalidated_config),
            )
            measurements.append(measurement)
            cache_observations.append(
                {
                    "code_map_hit": code_map_hit,
                    "cold_report_probe_hit": cold_probe.value is not None,
                    "warm_report_hit": True,
                    "invalidated_report_probe_hit": invalidated_probe.value is not None,
                }
            )
        medians = {name: round(statistics.median(item[name] for item in measurements), 6) for name in measurements[0]}
        return {
            "operation": (
                "Modwire uncached architecture reporting"
                if self.analysis_only
                else "Modwire cached-map and architecture-report phases"
            ),
            "root": str(self.root),
            "language": self.language,
            "files_checked": files_checked,
            "repetitions": self.repetitions,
            "configuration_seed": self.configuration_seed,
            "max_process_seconds": self.max_process_seconds,
            "median_seconds": medians,
            "cache_observations": cache_observations,
        }

    def _load_code_map_cache(self, path: Path) -> CodeMap:
        serialized = json.loads(path.read_text())
        payload = serialized.get("payload", serialized)
        return CodeMap.model_validate(payload)

    def _phase[Result](
        self,
        repetition: int,
        scenario: str,
        phase: str,
        operation: Callable[[], Result],
    ) -> tuple[Result, float]:
        self.current_scenario = scenario
        self.current_phase = phase
        print(
            json.dumps(
                {
                    "event": "phase_started",
                    "repetition": repetition,
                    "scenario": scenario,
                    "phase": phase,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        started = time.perf_counter()
        result = operation()
        duration = time.perf_counter() - started
        self._emit_phase(repetition, scenario, phase, duration, skipped=False)
        return result, duration

    def _skipped_phase(self, repetition: int, scenario: str, phase: str) -> float:
        self._emit_phase(repetition, scenario, phase, 0.0, skipped=True)
        return 0.0

    def _emit_phase(self, repetition: int, scenario: str, phase: str, duration: float, *, skipped: bool) -> None:
        print(
            json.dumps(
                {
                    "event": "phase",
                    "repetition": repetition,
                    "scenario": scenario,
                    "phase": phase,
                    "seconds": round(duration, 6),
                    "skipped": skipped,
                },
                sort_keys=True,
            ),
            flush=True,
        )


if __name__ == "__main__":
    raise SystemExit(ReportBenchmark.main())
