from __future__ import annotations

import argparse
import json
from pathlib import Path


class ScanBenchmarkFixture:
    def __init__(
        self, root: Path, source_template: Path, included_files: int, excluded_directories: int, excluded_files: int
    ) -> None:
        self.root = root
        self.source_template = source_template
        self.included_files = included_files
        self.excluded_directories = excluded_directories
        self.excluded_files = excluded_files

    @classmethod
    def main(cls) -> int:
        parser = argparse.ArgumentParser(description="Create a neutral source tree for the scan-pruning benchmark.")
        parser.add_argument("--root", type=Path, required=True)
        parser.add_argument("--source-template", type=Path, required=True)
        parser.add_argument("--included-files", type=int, default=100)
        parser.add_argument("--excluded-directories", type=int, default=100)
        parser.add_argument("--excluded-files", type=int, default=1000)
        arguments = parser.parse_args()
        fixture = cls(
            arguments.root,
            arguments.source_template,
            arguments.included_files,
            arguments.excluded_directories,
            arguments.excluded_files,
        )
        fixture.create()
        return 0

    def create(self) -> None:
        if min(self.included_files, self.excluded_directories, self.excluded_files) < 1:
            raise ValueError("Every fixture dimension must be at least one.")
        if self.root.exists() and any(self.root.iterdir()):
            raise RuntimeError(f"Fixture root must be absent or empty: {self.root}")
        if not self.source_template.is_file() or not self.source_template.suffix:
            raise RuntimeError(f"Source template must be a file with an extension: {self.source_template}")
        source = self.source_template.read_text(encoding="utf-8")
        suffix = self.source_template.suffix
        included_root = self.root / "example_source"
        included_root.mkdir(parents=True, exist_ok=True)
        for index in range(self.included_files):
            (included_root / f"example_{index:05d}{suffix}").write_text(source, encoding="utf-8")
        excluded_root = self.root / "example_excluded"
        for directory_index in range(self.excluded_directories):
            directory = excluded_root / f"segment_{directory_index:05d}"
            directory.mkdir(parents=True, exist_ok=True)
            for file_index in range(self.excluded_files):
                (directory / f"example_{file_index:05d}{suffix}").write_text(source, encoding="utf-8")
        manifest = {
            "included_files": self.included_files,
            "excluded_directories": self.excluded_directories,
            "excluded_files_per_directory": self.excluded_files,
            "excluded_source_files": self.excluded_directories * self.excluded_files,
            "source_extension": suffix,
        }
        (self.root / "fixture.json").write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")
        print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(ScanBenchmarkFixture.main())
