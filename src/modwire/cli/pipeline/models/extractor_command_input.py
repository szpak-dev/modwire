from ....shared.values.models.value_model import ValueModel
from .extractor_source_input import ExtractorSourceInput


class ExtractorCommandInput(ValueModel):
    batch: bool
    sources: tuple[ExtractorSourceInput, ...]
