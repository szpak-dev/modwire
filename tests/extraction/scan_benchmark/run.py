from __future__ import annotations

import argparse
import importlib
import json
import statistics
import time
from pathlib import Path
from typing import Any, cast


class ScanBenchmark:
    def __init__(
        self,
        root: Path,
        language: str,
        excluded_patterns: tuple[str, ...],
        repetitions: int,
        api: str,
    ) -> None:
        self.root = root.resolve()
        self.language = language
        self.excluded_patterns = excluded_patterns
        self.repetitions = repetitions
        self.api = api

    @classmethod
    def main(cls) -> int:
        parser = argparse.ArgumentParser(description="Measure full extraction over a caller-selected scan root.")
        parser.add_argument("--root", type=Path, required=True)
        parser.add_argument("--language", default="python")
        parser.add_argument("--excluded-pattern", action="append", default=[])
        parser.add_argument("--repeat", type=int, default=5)
        parser.add_argument("--api", choices=("current", "legacy"), default="current")
        arguments = parser.parse_args()
        if arguments.repeat < 1:
            parser.error("--repeat must be at least one")
        benchmark = cls(
            arguments.root,
            arguments.language,
            tuple(arguments.excluded_pattern),
            arguments.repeat,
            arguments.api,
        )
        print(json.dumps(benchmark.measure(), indent=2, sort_keys=True))
        return 0

    def measure(self) -> dict[str, Any]:
        if not self.root.is_dir():
            raise RuntimeError(f"Benchmark root is not a directory: {self.root}")
        application_module = importlib.import_module("modwire.application")
        application_type = getattr(application_module, "ModwireApplication")
        application = application_type.create()
        policy = self.policy(application_module)
        durations: list[float] = []
        measurements: list[dict[str, int | None]] = []
        for _ in range(self.repetitions):
            started = time.perf_counter()
            code_map = application.generate_map(self.language, str(self.root), policy)
            durations.append(time.perf_counter() - started)
            extraction = code_map.extraction
            measurements.append(
                {
                    "files_found": extraction.files_found,
                    "files_excluded": extraction.files_excluded,
                    "directories_pruned": getattr(extraction, "directories_pruned", None),
                    "files_built": len(extraction.files),
                    "modules_built": len(extraction.modules),
                }
            )
        if any(measurement != measurements[0] for measurement in measurements[1:]):
            raise RuntimeError(f"Extraction metrics changed between runs: {measurements}")
        return {
            "api": self.api,
            "operation": "ModwireApplication.generate_map",
            "root": str(self.root),
            "language": self.language,
            "excluded_patterns": list(self.excluded_patterns),
            "repetitions": self.repetitions,
            "runs_seconds": [round(duration, 6) for duration in durations],
            "median_seconds": round(statistics.median(durations), 6),
            "extraction": measurements[0],
        }

    def policy(self, application_module: Any) -> object:
        if self.api == "legacy":
            return self.excluded_patterns
        policy_type = getattr(application_module, "ScanPolicy")
        return cast(object, policy_type(excluded_patterns=self.excluded_patterns))


if __name__ == "__main__":
    raise SystemExit(ScanBenchmark.main())
