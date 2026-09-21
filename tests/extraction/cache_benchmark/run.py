from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

from modwire.application import CacheOptions, ModwireApplication, ScanPolicy


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
    ) -> None:
        self.root = root.resolve()
        self.language = language
        self.cache_directory = cache_directory.resolve()
        self.namespace = namespace
        self.source = source.resolve()
        self.replacement = replacement.resolve()
        self.repetitions = repetitions

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
        arguments = parser.parse_args()
        if arguments.repeat < 1:
            parser.error("--repeat must be at least one")
        benchmark = cls(
            arguments.root,
            arguments.language,
            arguments.cache_directory,
            arguments.cache_namespace,
            arguments.incremental_source,
            arguments.replacement_source,
            arguments.repeat,
        )
        print(json.dumps(benchmark.measure(), indent=2, sort_keys=True))
        return 0

    def measure(self) -> dict[str, Any]:
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
        config = application.configure({"shape": {"realms": [{"name": "example-source", "match": "**"}]}})
        request = application.extraction.request(self.language, str(self.root))
        measurements: list[dict[str, float]] = []
        try:
            for _ in range(self.repetitions):
                application.clear_cache(options)
                self.source.write_bytes(original)

                started = time.perf_counter()
                cold_snapshot = application.cli.extract_cached(request, policy, options)
                cold_extraction = time.perf_counter() - started

                started = time.perf_counter()
                cold_map = application.extraction.generate_map(self.language, cold_snapshot.extraction)
                dependency_resolution = time.perf_counter() - started
                application.cli.store_code_map(cold_snapshot, cold_map, options)

                queryable_map = application.generate_queryable_map_cached(self.language, self.root, policy, options)
                started = time.perf_counter()
                application.analyze_cached(queryable_map, config, options)
                cold_reporting = time.perf_counter() - started

                started = time.perf_counter()
                warm_snapshot = application.cli.extract_cached(request, policy, options)
                warm_freshness = time.perf_counter() - started

                started = time.perf_counter()
                warm_map = application.cli.cached_code_map(warm_snapshot, options)
                dependency_reuse = time.perf_counter() - started
                if warm_map is None:
                    raise RuntimeError("Warm CodeMap cache entry was not reusable.")

                started = time.perf_counter()
                application.analyze_cached(queryable_map, config, options)
                reporting_reuse = time.perf_counter() - started

                self.source.write_bytes(replacement)
                started = time.perf_counter()
                incremental_snapshot = application.cli.extract_cached(request, policy, options)
                incremental_extraction = time.perf_counter() - started

                started = time.perf_counter()
                application.extraction.generate_map(self.language, incremental_snapshot.extraction)
                incremental_resolution = time.perf_counter() - started

                measurements.append(
                    {
                        "cold_discovery_freshness_and_parsing": cold_extraction,
                        "estimated_cold_parsing": max(0.0, cold_extraction - warm_freshness),
                        "cold_dependency_resolution": dependency_resolution,
                        "cold_reporting": cold_reporting,
                        "warm_discovery_freshness": warm_freshness,
                        "warm_dependency_reuse": dependency_reuse,
                        "warm_reporting_reuse": reporting_reuse,
                        "incremental_discovery_freshness_and_changed_parsing": incremental_extraction,
                        "estimated_incremental_changed_parsing": max(0.0, incremental_extraction - warm_freshness),
                        "incremental_dependency_resolution": incremental_resolution,
                    }
                )
        finally:
            self.source.write_bytes(original)
        medians = {name: round(statistics.median(item[name] for item in measurements), 6) for name in measurements[0]}
        return {
            "operation": "Modwire incremental cache phases",
            "root": str(self.root),
            "language": self.language,
            "repetitions": self.repetitions,
            "median_seconds": medians,
            "remaining_warm_filesystem_cost": (
                "Every included source is opened and SHA-256 hashed to prove freshness; warm runs then deserialize "
                "the exact manifest CodeMap and report entries."
            ),
            "parsing_estimate": (
                "Estimated parsing subtracts the warm freshness-and-source-reuse median from extraction time; "
                "dependency resolution and reporting are measured independently."
            ),
        }


if __name__ == "__main__":
    raise SystemExit(CacheBenchmark.main())
