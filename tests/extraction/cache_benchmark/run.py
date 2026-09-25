from __future__ import annotations

import argparse
import json
import signal
import statistics
import time
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import Any

from modwire.application import CacheOptions, ModwireApplication, ScanPolicy

from .benchmark_process_timeout import BenchmarkProcessTimeout


class CacheBenchmark:
    def __init__(
        self,
        root: Path,
        language: str,
        cache_directory: Path,
        namespace: str,
        source: Path,
        replacement: Path,
        repetitions: int,
        max_process_seconds: float,
    ) -> None:
        self.root = root.resolve()
        self.language = language
        self.cache_directory = cache_directory.resolve()
        self.namespace = namespace
        self.source = source.resolve()
        self.replacement = replacement.resolve()
        self.repetitions = repetitions
        self.max_process_seconds = max_process_seconds
        self.current_scenario = "setup"
        self.current_phase = "validation"

    @classmethod
    def main(cls) -> int:
        parser = argparse.ArgumentParser(description="Measure cold, warm, and incremental Modwire cache phases.")
        parser.add_argument("--root", type=Path, required=True)
        parser.add_argument("--language", required=True)
        parser.add_argument("--cache-directory", type=Path, required=True)
        parser.add_argument("--cache-namespace", default="example-benchmark")
        parser.add_argument("--incremental-source", type=Path, required=True)
        parser.add_argument("--replacement-source", type=Path, required=True)
        parser.add_argument("--repeat", type=int, default=3)
        parser.add_argument("--max-process-seconds", type=float, default=10.0)
        arguments = parser.parse_args()
        if arguments.repeat < 1:
            parser.error("--repeat must be at least one")
        if arguments.max_process_seconds <= 0:
            parser.error("--max-process-seconds must be greater than zero")
        if not hasattr(signal, "setitimer"):
            parser.error("hard benchmark timeouts require signal.setitimer")
        benchmark = cls(
            arguments.root,
            arguments.language,
            arguments.cache_directory,
            arguments.cache_namespace,
            arguments.incremental_source,
            arguments.replacement_source,
            arguments.repeat,
            arguments.max_process_seconds,
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

    def measure(self) -> dict[str, Any]:
        def timeout_handler(_signal_number: int, _frame: FrameType | None) -> None:
            raise BenchmarkProcessTimeout(
                self.current_scenario,
                self.current_phase,
                self.max_process_seconds,
            )

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
        if not self.source.is_file() or self.root not in self.source.parents:
            raise RuntimeError(f"Incremental source must be a file beneath the benchmark root: {self.source}")
        if not self.replacement.is_file():
            raise RuntimeError(f"Replacement source must be a file: {self.replacement}")
        original = self.source.read_bytes()
        replacement = self.replacement.read_bytes()
        if original == replacement:
            raise RuntimeError("Replacement source must differ from the incremental source.")
        application = ModwireApplication.create()
        policy = ScanPolicy()
        options = CacheOptions(
            directory=str(self.cache_directory),
            namespace=self.namespace,
            max_bytes=2 * 1024 * 1024 * 1024,
        )
        measurements: list[dict[str, float]] = []
        try:
            for repetition in range(1, self.repetitions + 1):
                self.current_scenario = "setup"
                self.current_phase = "cache_clear"
                application.clear_cache(options)
                self.current_phase = "source_restore"
                self.source.write_bytes(original)
                request = application.extraction.request(self.language, str(self.root))
                measurement: dict[str, float] = {}

                total_started = time.perf_counter()
                cold_plan, measurement["cold_inventory"] = self._phase(
                    repetition, "cold", "inventory", lambda: application.cli.prepare_cache(request, policy)
                )
                cold_cached_map, measurement["cold_code_map_loading"] = self._phase(
                    repetition,
                    "cold",
                    "code_map_loading",
                    lambda: application.cli.cached_code_map(cold_plan, options),
                )
                if cold_cached_map.value is not None:
                    raise RuntimeError("Cold CodeMap cache probe unexpectedly hit.")
                cold_sources, measurement["cold_source_loading"] = self._phase(
                    repetition,
                    "cold",
                    "source_loading",
                    lambda: application.cli.cached_sources(request, cold_plan, options),
                )
                _, measurement["cold_manifest_maintenance"] = self._phase(
                    repetition,
                    "cold",
                    "manifest_maintenance",
                    lambda: application.cli.maintain_manifest(cold_plan, options),
                )
                cold_map, measurement["cold_dependency_resolution"] = self._phase(
                    repetition,
                    "cold",
                    "dependency_resolution",
                    lambda: application.extraction.generate_map(self.language, cold_sources.value),
                )
                _, measurement["cold_code_map_storage"] = self._phase(
                    repetition,
                    "cold",
                    "code_map_storage",
                    lambda: application.cli.store_code_map(cold_plan, cold_map, options),
                )
                _, measurement["cold_capacity_maintenance"] = self._phase(
                    repetition,
                    "cold",
                    "capacity_maintenance",
                    lambda: application.cli.maintain_cache(options),
                )
                measurement["cold_total"] = time.perf_counter() - total_started
                self._emit_total(repetition, "cold", measurement["cold_total"])

                total_started = time.perf_counter()
                warm_plan, measurement["warm_inventory"] = self._phase(
                    repetition, "warm", "inventory", lambda: application.cli.prepare_cache(request, policy)
                )
                warm_cached_map, measurement["warm_code_map_loading"] = self._phase(
                    repetition,
                    "warm",
                    "code_map_loading",
                    lambda: application.cli.cached_code_map(warm_plan, options),
                )
                if warm_cached_map.value is None:
                    raise RuntimeError("Warm CodeMap cache entry was not reusable.")
                _, measurement["warm_capacity_maintenance"] = self._phase(
                    repetition,
                    "warm",
                    "capacity_maintenance",
                    lambda: application.cli.maintain_cache(options),
                )
                measurement["warm_source_loading"] = 0.0
                measurement["warm_manifest_maintenance"] = 0.0
                measurement["warm_total"] = time.perf_counter() - total_started
                self._emit_total(repetition, "warm", measurement["warm_total"])

                self.current_scenario = "setup"
                self.current_phase = "source_replacement"
                self.source.write_bytes(replacement)
                total_started = time.perf_counter()
                incremental_plan, measurement["incremental_inventory"] = self._phase(
                    repetition,
                    "incremental",
                    "inventory",
                    lambda: application.cli.prepare_cache(request, policy),
                )
                incremental_cached_map, measurement["incremental_code_map_loading"] = self._phase(
                    repetition,
                    "incremental",
                    "code_map_loading",
                    lambda: application.cli.cached_code_map(incremental_plan, options),
                )
                if incremental_cached_map.value is not None:
                    raise RuntimeError("Changed source unexpectedly reused the complete CodeMap.")
                incremental_sources, measurement["incremental_source_loading"] = self._phase(
                    repetition,
                    "incremental",
                    "source_loading",
                    lambda: application.cli.cached_sources(request, incremental_plan, options),
                )
                _, measurement["incremental_manifest_maintenance"] = self._phase(
                    repetition,
                    "incremental",
                    "manifest_maintenance",
                    lambda: application.cli.maintain_manifest(incremental_plan, options),
                )
                incremental_map, measurement["incremental_dependency_resolution"] = self._phase(
                    repetition,
                    "incremental",
                    "dependency_resolution",
                    lambda: application.extraction.generate_map(self.language, incremental_sources.value),
                )
                _, measurement["incremental_code_map_storage"] = self._phase(
                    repetition,
                    "incremental",
                    "code_map_storage",
                    lambda: application.cli.store_code_map(incremental_plan, incremental_map, options),
                )
                _, measurement["incremental_capacity_maintenance"] = self._phase(
                    repetition,
                    "incremental",
                    "capacity_maintenance",
                    lambda: application.cli.maintain_cache(options),
                )
                measurement["incremental_total"] = time.perf_counter() - total_started
                self._emit_total(repetition, "incremental", measurement["incremental_total"])
                measurements.append(measurement)
        finally:
            self.source.write_bytes(original)
        medians = {name: round(statistics.median(item[name] for item in measurements), 6) for name in measurements[0]}
        return {
            "operation": "Modwire cold, fully warm, and incremental cache phases",
            "root": str(self.root),
            "language": self.language,
            "repetitions": self.repetitions,
            "max_process_seconds": self.max_process_seconds,
            "median_seconds": medians,
            "warm_skipped_stages": ["source_loading", "manifest_maintenance"],
            "remaining_warm_filesystem_cost": (
                "Every included source is opened and SHA-256 hashed during inventory. The exact CodeMap is then "
                "loaded directly, and the capacity ledger is checked without enumerating cache entries."
            ),
        }

    def _phase[Result](
        self,
        repetition: int,
        scenario: str,
        phase: str,
        operation: Callable[[], Result],
    ) -> tuple[Result, float]:
        self.current_scenario = scenario
        self.current_phase = phase
        started = time.perf_counter()
        result = operation()
        duration = time.perf_counter() - started
        print(
            json.dumps(
                {
                    "event": "phase",
                    "repetition": repetition,
                    "scenario": scenario,
                    "phase": phase,
                    "seconds": round(duration, 6),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return result, duration

    def _emit_total(self, repetition: int, scenario: str, duration: float) -> None:
        print(
            json.dumps(
                {
                    "event": "scenario",
                    "repetition": repetition,
                    "scenario": scenario,
                    "seconds": round(duration, 6),
                },
                sort_keys=True,
            ),
            flush=True,
        )


if __name__ == "__main__":
    raise SystemExit(CacheBenchmark.main())
