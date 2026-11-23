import argparse
from pathlib import Path

from .argument_default import ArgumentDefault


class BenchmarkArguments(argparse.Namespace):
    config: Path
    clone_root: Path | ArgumentDefault
    refresh: bool
    repeat: int
    only: list[str]
    profile_dir: Path | ArgumentDefault
    profile_max_workers: int | ArgumentDefault
