from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ....extraction.extractors.models.batch_config import BatchConfig
from .plan import SourceBatchPlan
from .planner import SourceBatchPlanner


@injectable(as_type=SourceBatchPlanner, qualifier="fixed")
@dataclass(frozen=True)
class FixedSourceBatchPlanner(SourceBatchPlanner):
    def plan(self, sources: tuple[Path, ...], config: BatchConfig) -> SourceBatchPlan:
        parallel = (
            config.parallel_threshold > 0 and len(sources) >= config.parallel_threshold and config.max_workers > 1
        )
        batch_size = config.parallel_size if parallel and config.parallel_size > 0 else config.size
        return SourceBatchPlan(
            parallel=parallel,
            batches=tuple(sources[start : start + batch_size] for start in range(0, len(sources), batch_size)),
        )
