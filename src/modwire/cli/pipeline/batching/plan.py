from dataclasses import dataclass

from ..models.source_entry import SourceEntry


@dataclass(frozen=True)
class SourceBatchPlan:
    parallel: bool
    batches: tuple[tuple[SourceEntry, ...], ...]
