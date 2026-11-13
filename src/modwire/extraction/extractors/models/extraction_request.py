from pydantic import Field

from ....shared.values.models.value_model import ValueModel
from ..domain import SourceExtractor
from .batch_config import BatchConfig
from .extractor_runtime import ExtractorRuntime


class ExtractionRequest(ValueModel):
    root: str
    strategy: SourceExtractor = Field(exclude=True)

    @property
    def runtime(self) -> ExtractorRuntime:
        return self.strategy.runtime

    @property
    def batch_config(self) -> BatchConfig:
        return self.strategy.batch_config
