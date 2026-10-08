from abc import ABC, abstractmethod
from pathlib import Path

from ....extraction.extractors.models.batch_config import BatchConfig
from .plan import SourceBatchPlan


class SourceBatchPlanner(ABC):
    @abstractmethod
    def plan(self, sources: tuple[Path, ...], config: BatchConfig) -> SourceBatchPlan:
        raise NotImplementedError
