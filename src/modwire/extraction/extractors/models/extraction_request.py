from ....shared.values.models.value_model import ValueModel
from .batch_config import BatchConfig
from .extractor_runtime import ExtractorRuntime


class ExtractionRequest(ValueModel):
    root: str
    runtime: ExtractorRuntime
    batch_config: BatchConfig
