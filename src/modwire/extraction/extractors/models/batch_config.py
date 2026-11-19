from ....shared.values.models.value_model import ValueModel
from .batch_planner_kind import BatchPlannerKind


class BatchConfig(ValueModel):
    size: int = 500
    parallel_threshold: int = 0
    parallel_size: int = 0
    max_workers: int = 1
    planner: BatchPlannerKind = BatchPlannerKind.FIXED
