from abc import ABC, abstractmethod

from ....extraction.extractors.models.batch_config import BatchConfig
from ..models.source_entry import SourceEntry
from .plan import SourceBatchPlan


class SourceBatchPlanner(ABC):
    @abstractmethod
    def plan(self, sources: tuple[SourceEntry, ...], config: BatchConfig) -> SourceBatchPlan:
        raise NotImplementedError
