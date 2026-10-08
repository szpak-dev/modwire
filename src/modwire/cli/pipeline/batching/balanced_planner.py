from dataclasses import dataclass
from pathlib import Path

from wireup import injectable

from ....extraction.extractors.models.batch_config import BatchConfig
from .plan import SourceBatchPlan
from .planner import SourceBatchPlanner


@injectable(as_type=SourceBatchPlanner, qualifier="balanced")
@dataclass(frozen=True)
class BalancedSourceBatchPlanner(SourceBatchPlanner):
    def plan(self, sources: tuple[Path, ...], config: BatchConfig) -> SourceBatchPlan:
        parallel = (
            config.parallel_threshold > 0 and len(sources) >= config.parallel_threshold and config.max_workers > 1
        )
        if not parallel:
            return SourceBatchPlan(
                parallel=False,
                batches=tuple(sources[start : start + config.size] for start in range(0, len(sources), config.size)),
            )
        if config.parallel_size <= 0:
            raise ValueError("Balanced source batching requires a positive parallel size.")
        worker_count = min(config.max_workers, len(sources))
        minimum_batch_count = (len(sources) + config.parallel_size - 1) // config.parallel_size
        batch_count = max(worker_count, minimum_batch_count)
        complete_wave_count = ((batch_count + worker_count - 1) // worker_count) * worker_count
        if complete_wave_count <= len(sources):
            batch_count = complete_wave_count
        return SourceBatchPlan(
            parallel=True,
            batches=tuple(sources[index::batch_count] for index in range(batch_count)),
        )
