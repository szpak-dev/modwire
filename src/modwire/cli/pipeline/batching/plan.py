from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceBatchPlan:
    parallel: bool
    batches: tuple[tuple[Path, ...], ...]
