from dataclasses import dataclass
from heapq import heapify, heappop, heappush

from wireup import injectable

from ....extraction.extractors.models.batch_config import BatchConfig
from ..models.pipeline_validation_error import PipelineValidationError
from ..models.pipeline_violation import PipelineViolation
from ..models.source_entry import SourceEntry
from .plan import SourceBatchPlan
from .planner import SourceBatchPlanner


@injectable(as_type=SourceBatchPlanner, qualifier="balanced")
@dataclass(frozen=True)
class BalancedSourceBatchPlanner(SourceBatchPlanner):
    def plan(self, sources: tuple[SourceEntry, ...], config: BatchConfig) -> SourceBatchPlan:
        parallel = (
            config.parallel_threshold > 0 and len(sources) >= config.parallel_threshold and config.max_workers > 1
        )
        if not parallel:
            return SourceBatchPlan(
                parallel=False,
                batches=tuple(sources[start : start + config.size] for start in range(0, len(sources), config.size)),
            )
        if config.parallel_size <= 0:
            raise PipelineValidationError(PipelineViolation.INVALID_PARALLEL_SIZE, str(config.parallel_size))
        worker_count = min(config.max_workers, len(sources))
        minimum_batch_count = (len(sources) + config.parallel_size - 1) // config.parallel_size
        batch_count = max(worker_count, minimum_batch_count)
        complete_wave_count = ((batch_count + worker_count - 1) // worker_count) * worker_count
        if complete_wave_count <= len(sources):
            batch_count = complete_wave_count
        batches: list[list[SourceEntry]] = [[] for _ in range(batch_count)]
        loads = [(0, 0, index) for index in range(batch_count)]
        heapify(loads)
        for source in sorted(sources, key=lambda item: item.line_count, reverse=True):
            line_count, file_count, index = heappop(loads)
            batches[index].append(source)
            file_count += 1
            if file_count < config.parallel_size:
                heappush(loads, (line_count + source.line_count, file_count, index))
        return SourceBatchPlan(parallel=True, batches=tuple(tuple(batch) for batch in batches))
