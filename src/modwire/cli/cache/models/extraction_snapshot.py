from ....shared.code.models.source_extraction import SourceExtraction
from ....shared.values.models.value_model import ValueModel
from .cache_key import CacheKey


class ExtractionSnapshot(ValueModel):
    extraction: SourceExtraction
    manifest: CacheKey
